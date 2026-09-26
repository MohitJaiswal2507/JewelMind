"""
Production Execution Service
Core business logic and state machine engine for shop-floor manufacturing operations.
Enforces strict state transitions, accurate bench/pause time calculations,
multi-tenant authorization, and authoritative ProductionStep/ScheduledTask linkage.
"""

import math
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple, Union

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.exceptions import AppException
from app.models.execution import OperationExecution
from app.models.production import Machine, ProductionOrder, Worker
from app.models.schedule import ScheduledTask
from app.models.specification import ProductionSpecification, ProductionStep
from app.schemas.execution import (
    ExecutionStatus,
    OperationExecutionCreate,
    OperationExecutionResponse,
    OperationExecutionTransitionRequest,
)

# Valid state transitions for shop-floor operations
VALID_TRANSITIONS: Dict[ExecutionStatus, Set[ExecutionStatus]] = {
    ExecutionStatus.PENDING: {ExecutionStatus.READY},
    ExecutionStatus.READY: {ExecutionStatus.IN_PROGRESS, ExecutionStatus.BLOCKED},
    ExecutionStatus.IN_PROGRESS: {
        ExecutionStatus.PAUSED,
        ExecutionStatus.COMPLETED,
        ExecutionStatus.BLOCKED,
    },
    ExecutionStatus.PAUSED: {ExecutionStatus.IN_PROGRESS, ExecutionStatus.BLOCKED},
    ExecutionStatus.BLOCKED: {ExecutionStatus.READY},
    # COMPLETED is terminal in J.1: no valid outward transitions
    ExecutionStatus.COMPLETED: set(),
}


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensures datetime is timezone-aware in UTC (normalizing SQLite naive datetimes)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def serialize_execution_response(execution: OperationExecution) -> OperationExecutionResponse:
    """
    Serializes an OperationExecution ORM instance into its response schema,
    denormalizing step and resource information for operator inspection.
    """
    step = execution.production_step
    worker = execution.worker
    machine = execution.machine

    return OperationExecutionResponse(
        id=execution.id,
        user_id=execution.user_id,
        production_order_id=execution.production_order_id,
        production_step_id=execution.production_step_id,
        scheduled_task_id=execution.scheduled_task_id,
        worker_id=execution.worker_id,
        machine_id=execution.machine_id,
        status=ExecutionStatus(execution.status),
        planned_start_time=execution.planned_start_time,
        planned_end_time=execution.planned_end_time,
        planned_duration_hours=execution.planned_duration_hours,
        actual_start_time=execution.actual_start_time,
        actual_end_time=execution.actual_end_time,
        actual_duration_hours=execution.actual_duration_hours,
        pause_duration_hours=execution.pause_duration_hours,
        last_paused_at=execution.last_paused_at,
        completed_at=execution.completed_at,
        operator_notes=execution.operator_notes,
        created_at=execution.created_at,
        updated_at=execution.updated_at,
        step_number=step.step_number if step else None,
        stage_name=step.stage_name if step else None,
        required_skill=step.required_skill if step else None,
        required_machine_type=step.required_machine_type if step else None,
        quality_checkpoint=step.quality_checkpoint if step else None,
        worker_name=worker.name if worker else None,
        machine_name=machine.name if machine else None,
    )


class ProductionExecutionService:
    """
    Foundational manufacturing execution service managing actual workshop
    operations, artisan transitions, timing reconciliation, and order tracking.
    """

    @staticmethod
    def initialize_order_executions(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
    ) -> List[OperationExecution]:
        """
        Initializes shop-floor execution records for a spec-backed production order.
        Creates all routing steps in advance:
        - Step 1 is marked READY.
        - Steps 2..N are marked PENDING.
        If matching ScheduledTasks exist, planned timing and allocations are copied.
        Idempotent: if already initialized, returns existing records without duplicates.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        # 1. Load order and verify ownership
        order_stmt = (
            select(ProductionOrder)
            .options(
                joinedload(ProductionOrder.specification).selectinload(ProductionSpecification.steps),
                selectinload(ProductionOrder.executions).joinedload(OperationExecution.production_step),
            )
            .where(ProductionOrder.id == order_id, ProductionOrder.user_id == user_id)
        )
        order = db.scalar(order_stmt)
        if not order:
            raise AppException(
                "Production order not found.",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        # 2. Check if executions have already been initialized (Idempotency / Duplicate protection)
        if order.executions and len(order.executions) > 0:
            # Sort by step_number and return existing executions
            sorted_existing = sorted(
                order.executions,
                key=lambda e: (e.production_step.step_number if e.production_step else 0),
            )
            return sorted_existing

        # 3. Check legacy order compatibility
        if not order.specification_id or not order.specification:
            raise AppException(
                "Cannot initialize step-based operation executions for a legacy order without a "
                "Production Specification. Only spec-backed orders with defined routing steps can be executed.",
                code="ORDER_LACKS_SPECIFICATION",
                status_code=400,
            )

        spec: ProductionSpecification = order.specification
        if spec.status != "approved":
            raise AppException(
                f"Cannot initialize executions for order bound to a '{spec.status}' specification. "
                "Specification must be approved.",
                code="SPECIFICATION_NOT_APPROVED",
                status_code=400,
            )

        if not spec.steps or len(spec.steps) == 0:
            raise AppException(
                "Associated production specification contains no routing steps.",
                code="SPECIFICATION_NO_STEPS",
                status_code=400,
            )

        sorted_steps = sorted(spec.steps, key=lambda s: s.step_number)

        # 4. Query any planned scheduled tasks for this order
        tasks_stmt = (
            select(ScheduledTask)
            .where(ScheduledTask.order_id == order.id)
            .order_by(ScheduledTask.sequence_order.asc(), ScheduledTask.start_time.asc())
        )
        scheduled_tasks: List[ScheduledTask] = list(db.scalars(tasks_stmt).all())

        # Map scheduled tasks by step/sequence order for planned timing alignment
        task_by_seq: Dict[int, ScheduledTask] = {
            t.sequence_order: t for t in scheduled_tasks
        }

        # 5. Build executions atomically
        executions_to_create: List[OperationExecution] = []
        for idx, step in enumerate(sorted_steps):
            # First operation begins READY; subsequent operations are PENDING
            initial_status = ExecutionStatus.READY.value if idx == 0 else ExecutionStatus.PENDING.value

            # Attempt matching to scheduled task
            matched_task: Optional[ScheduledTask] = task_by_seq.get(step.step_number)
            if not matched_task and idx < len(scheduled_tasks):
                # Fallback to index-based sequence match if step_number offset differs
                matched_task = scheduled_tasks[idx]

            planned_start = matched_task.start_time if matched_task else None
            planned_end = matched_task.end_time if matched_task else None
            if matched_task:
                planned_duration = matched_task.duration_hours
                assigned_worker_id = matched_task.worker_id
                assigned_machine_id = matched_task.machine_id
                matched_task_id = matched_task.id
            else:
                # Direct unscheduled duration estimation
                calc_dur = step.base_hours + (step.per_unit_hours * max(1, order.quantity))
                planned_duration = float(max(1, math.ceil(calc_dur)))
                assigned_worker_id = None
                assigned_machine_id = None
                matched_task_id = None

            execution = OperationExecution(
                id=uuid.uuid4(),
                user_id=user_id,
                production_order_id=order.id,
                production_step_id=step.id,
                scheduled_task_id=matched_task_id,
                worker_id=assigned_worker_id,
                machine_id=assigned_machine_id,
                status=initial_status,
                planned_start_time=planned_start,
                planned_end_time=planned_end,
                planned_duration_hours=planned_duration,
                actual_start_time=None,
                actual_end_time=None,
                actual_duration_hours=None,
                pause_duration_hours=0.0,
                last_paused_at=None,
                completed_at=None,
                operator_notes=None,
            )
            executions_to_create.append(execution)

        # 6. Commit atomically
        try:
            db.add_all(executions_to_create)
            db.commit()
            for ex in executions_to_create:
                db.refresh(ex)
        except Exception:
            db.rollback()
            raise

        # Attach step relationships for response mapping
        for idx, ex in enumerate(executions_to_create):
            ex.production_step = sorted_steps[idx]

        return executions_to_create

    @staticmethod
    def get_order_executions(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
    ) -> List[OperationExecution]:
        """
        Retrieves all operation executions for a given production order,
        ensuring tenant isolation and sorted by routing step number.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        # Verify order exists and belongs to user
        order = db.scalar(
            select(ProductionOrder).where(
                ProductionOrder.id == order_id,
                ProductionOrder.user_id == user_id,
            )
        )
        if not order:
            raise AppException("Production order not found.", code="ORDER_NOT_FOUND", status_code=404)

        stmt = (
            select(OperationExecution)
            .options(
                joinedload(OperationExecution.production_step),
                joinedload(OperationExecution.worker),
                joinedload(OperationExecution.machine),
                joinedload(OperationExecution.scheduled_task),
            )
            .where(
                OperationExecution.production_order_id == order_id,
                OperationExecution.user_id == user_id,
            )
        )
        executions = list(db.scalars(stmt).all())
        executions.sort(key=lambda e: (e.production_step.step_number if e.production_step else 0))
        return executions

    @staticmethod
    def get_execution_by_id(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
    ) -> OperationExecution:
        """
        Retrieves a single operation execution with loaded relationships,
        enforcing multi-tenant isolation.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(execution_id, str):
            execution_id = uuid.UUID(execution_id)

        stmt = (
            select(OperationExecution)
            .options(
                joinedload(OperationExecution.production_step),
                joinedload(OperationExecution.worker),
                joinedload(OperationExecution.machine),
                joinedload(OperationExecution.scheduled_task),
            )
            .where(
                OperationExecution.id == execution_id,
                OperationExecution.user_id == user_id,
            )
        )
        execution = db.scalar(stmt)
        if not execution:
            raise AppException(
                "Operation execution not found.",
                code="EXECUTION_NOT_FOUND",
                status_code=404,
            )
        return execution

    @staticmethod
    def transition_execution(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
        req: OperationExecutionTransitionRequest,
    ) -> OperationExecution:
        """
        Executes a validated state transition on an OperationExecution.
        Updates shop-floor timestamps, calculates elapsed/pause durations,
        validates resource ownership, and commits atomically.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(execution_id, str):
            execution_id = uuid.UUID(execution_id)

        # 1. Load execution with tenant isolation
        execution = ProductionExecutionService.get_execution_by_id(
            db=db,
            user_id=user_id,
            execution_id=execution_id,
        )

        current_status = ExecutionStatus(execution.status)
        target_status = req.target_status
        now = datetime.now(timezone.utc)

        # 2. Immutability check: once completed, execution cannot be restarted
        if current_status == ExecutionStatus.COMPLETED:
            raise AppException(
                "Completed operation executions are immutable and cannot be transitioned.",
                code="EXECUTION_ALREADY_COMPLETED",
                status_code=409,
            )

        # 3. Transition validation against strict state machine
        allowed_targets = VALID_TRANSITIONS.get(current_status, set())
        if target_status not in allowed_targets:
            raise AppException(
                f"Invalid execution transition from '{current_status.value}' to '{target_status.value}'.",
                code="INVALID_EXECUTION_TRANSITION",
                status_code=400,
            )

        # 4. Optional resource ownership validation
        if req.worker_id is not None:
            worker = db.scalar(
                select(Worker).where(Worker.id == req.worker_id, Worker.user_id == user_id)
            )
            if not worker:
                raise AppException("Worker not found or belongs to another tenant.", code="WORKER_NOT_FOUND", status_code=404)
            execution.worker_id = worker.id
            execution.worker = worker

        if req.machine_id is not None:
            machine = db.scalar(
                select(Machine).where(Machine.id == req.machine_id, Machine.user_id == user_id)
            )
            if not machine:
                raise AppException("Machine not found or belongs to another tenant.", code="MACHINE_NOT_FOUND", status_code=404)
            execution.machine_id = machine.id
            execution.machine = machine

        # 5. Apply timing logic according to the transition
        if current_status == ExecutionStatus.READY and target_status == ExecutionStatus.IN_PROGRESS:
            # Operation starts: record actual_start_time if not already set
            if not execution.actual_start_time:
                execution.actual_start_time = now

        elif current_status == ExecutionStatus.IN_PROGRESS and target_status == ExecutionStatus.PAUSED:
            # Operation pauses: record pause start timestamp
            execution.last_paused_at = now

        elif current_status == ExecutionStatus.PAUSED and target_status == ExecutionStatus.IN_PROGRESS:
            # Operation resumes: reconcile pause duration and reset pause mark
            last_p = _ensure_utc(execution.last_paused_at)
            if last_p:
                pause_delta_hours = (now - last_p).total_seconds() / 3600.0
                execution.pause_duration_hours += max(0.0, pause_delta_hours)
                execution.last_paused_at = None

        elif current_status == ExecutionStatus.IN_PROGRESS and target_status == ExecutionStatus.COMPLETED:
            # Operation completes: record end timestamp and calculate net duration
            execution.actual_end_time = now
            execution.completed_at = now

            act_start = _ensure_utc(execution.actual_start_time)
            if act_start:
                total_elapsed_hours = (now - act_start).total_seconds() / 3600.0
                net_duration = total_elapsed_hours - execution.pause_duration_hours
                execution.actual_duration_hours = max(0.0, round(net_duration, 4))
            else:
                execution.actual_duration_hours = 0.0

        elif target_status == ExecutionStatus.BLOCKED:
            # If blocking from IN_PROGRESS, mark pause timestamp to prevent double-counting duration
            if current_status == ExecutionStatus.IN_PROGRESS:
                execution.last_paused_at = now

        elif current_status == ExecutionStatus.BLOCKED and target_status == ExecutionStatus.READY:
            # Unblocking back to READY: if paused while in progress, accumulate pause duration
            last_p = _ensure_utc(execution.last_paused_at)
            if last_p:
                pause_delta_hours = (now - last_p).total_seconds() / 3600.0
                execution.pause_duration_hours += max(0.0, pause_delta_hours)
                execution.last_paused_at = None

        # 6. Apply status and notes
        execution.status = target_status.value
        if req.operator_notes is not None:
            if execution.operator_notes:
                execution.operator_notes = f"{execution.operator_notes}\n[{now.strftime('%Y-%m-%d %H:%M:%S UTC')}] {req.operator_notes}"
            else:
                execution.operator_notes = req.operator_notes

        # 7. Atomically commit transition
        try:
            db.commit()
            db.refresh(execution)
        except Exception:
            db.rollback()
            raise

        return execution

    @staticmethod
    def create_execution(
        db: Session,
        user_id: Union[str, uuid.UUID],
        create_in: OperationExecutionCreate,
    ) -> OperationExecution:
        """
        Manually creates an OperationExecution record with strict linkage validation:
        - Verifies that the ProductionStep belongs to the ProductionSpecification of the ProductionOrder.
        - Verifies that any referenced ScheduledTask belongs to the same order and user.
        - Verifies that any referenced Worker or Machine belongs to the user.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # 1. Validate ProductionOrder existence & ownership
        order_stmt = (
            select(ProductionOrder)
            .options(joinedload(ProductionOrder.specification).selectinload(ProductionSpecification.steps))
            .where(
                ProductionOrder.id == create_in.production_order_id,
                ProductionOrder.user_id == user_id,
            )
        )
        order = db.scalar(order_stmt)
        if not order:
            raise AppException("Production order not found.", code="ORDER_NOT_FOUND", status_code=404)

        if not order.specification:
            raise AppException(
                "Production order has no associated Production Specification.",
                code="ORDER_LACKS_SPECIFICATION",
                status_code=400,
            )

        # 2. Validate ProductionStep belongs to this order's specification
        valid_step_ids = {s.id for s in order.specification.steps}
        if create_in.production_step_id not in valid_step_ids:
            raise AppException(
                "ProductionStep does not belong to the specification associated with this production order.",
                code="INVALID_STEP_ORDER_LINKAGE",
                status_code=400,
            )

        step = next(s for s in order.specification.steps if s.id == create_in.production_step_id)

        # 3. Validate ScheduledTask linkage if provided
        matched_task: Optional[ScheduledTask] = None
        if create_in.scheduled_task_id is not None:
            task = db.scalar(
                select(ScheduledTask).where(ScheduledTask.id == create_in.scheduled_task_id)
            )
            if not task:
                raise AppException("Scheduled task not found.", code="TASK_NOT_FOUND", status_code=404)
            if task.order_id != order.id:
                raise AppException(
                    "Scheduled task does not belong to this production order.",
                    code="TASK_ORDER_MISMATCH",
                    status_code=400,
                )
            matched_task = task

        # 4. Validate Worker & Machine ownership
        if create_in.worker_id is not None:
            worker = db.scalar(
                select(Worker).where(Worker.id == create_in.worker_id, Worker.user_id == user_id)
            )
            if not worker:
                raise AppException("Worker not found or belongs to another tenant.", code="WORKER_NOT_FOUND", status_code=404)

        if create_in.machine_id is not None:
            machine = db.scalar(
                select(Machine).where(Machine.id == create_in.machine_id, Machine.user_id == user_id)
            )
            if not machine:
                raise AppException("Machine not found or belongs to another tenant.", code="MACHINE_NOT_FOUND", status_code=404)

        # 5. Timing defaults
        planned_start = matched_task.start_time if matched_task else None
        planned_end = matched_task.end_time if matched_task else None
        if matched_task:
            planned_duration = matched_task.duration_hours
        else:
            calc_dur = step.base_hours + (step.per_unit_hours * max(1, order.quantity))
            planned_duration = float(max(1, math.ceil(calc_dur)))

        execution = OperationExecution(
            id=uuid.uuid4(),
            user_id=user_id,
            production_order_id=order.id,
            production_step_id=step.id,
            scheduled_task_id=create_in.scheduled_task_id,
            worker_id=create_in.worker_id,
            machine_id=create_in.machine_id,
            status=ExecutionStatus.PENDING.value,
            planned_start_time=planned_start,
            planned_end_time=planned_end,
            planned_duration_hours=planned_duration,
            actual_start_time=None,
            actual_end_time=None,
            actual_duration_hours=None,
            pause_duration_hours=0.0,
            last_paused_at=None,
            completed_at=None,
            operator_notes=create_in.operator_notes,
        )

        try:
            db.add(execution)
            db.commit()
            db.refresh(execution)
        except Exception:
            db.rollback()
            raise

        execution.production_step = step
        return execution


production_execution_service = ProductionExecutionService()
