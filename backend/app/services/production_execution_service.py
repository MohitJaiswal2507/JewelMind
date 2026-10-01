"""
Production Execution Service
Core business logic and state machine engine for shop-floor manufacturing operations.
Enforces strict state transitions, accurate bench/pause time calculations,
multi-tenant authorization, authoritative ProductionStep/ScheduledTask linkage,
and automatic sequential routing progression (Phase J.2).
"""

import math
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple, Union

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.exceptions import AppException
from app.models.execution import MaterialConsumption, OperationExecution, QualityCheck
from app.models.production import Machine, ProductionOrder, Worker
from app.models.schedule import ScheduledTask
from app.models.specification import (
    ProductionGemstone,
    ProductionMaterial,
    ProductionSpecification,
    ProductionStep,
)
from app.schemas.execution import (
    DefectSeverity,
    ExecutionQualitySummaryItem,
    ExecutionStatus,
    MaterialConsumptionCreate,
    MaterialConsumptionResponse,
    MaterialSummaryItem,
    OperationExecutionCreate,
    OperationExecutionListResponse,
    OperationExecutionResponse,
    OperationExecutionTransitionRequest,
    OrderMaterialSummaryResponse,
    OrderQualitySummaryResponse,
    QualityCheckCreate,
    QualityCheckResponse,
    QualityCheckResult,
    ReworkExecutionCreate,
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
    # COMPLETED is terminal: no valid outward transitions
    ExecutionStatus.COMPLETED: set(),
}


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensures datetime is timezone-aware in UTC (normalizing SQLite naive datetimes)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_worker_skills(worker: Optional[Worker]) -> Set[str]:
    """Extracts normalized set of craft skills possessed by a worker."""
    if not worker or not worker.skill:
        return set()
    raw = worker.skill.strip()
    if raw.startswith("[") and raw.endswith("]"):
        import json
        try:
            items = json.loads(raw)
            if isinstance(items, list):
                return {str(i).strip().lower() for i in items if str(i).strip()}
        except Exception:
            pass
    return {s.strip().lower() for s in raw.split(",") if s.strip()}


def is_worker_skill_eligible(worker: Optional[Worker], required_skill: Optional[str]) -> bool:
    """
    Determines if a worker is eligible for an operation requiring a specific craft skill.
    Matching is deterministic and case-normalized.
    - If required_skill is empty, None, 'none', or 'general', any worker is eligible.
    - If worker has 'general' skill, the worker is eligible as fallback.
    - Otherwise, worker must possess the required skill.
    """
    if not required_skill or not required_skill.strip():
        return True
    req = required_skill.strip().lower()
    if req in ("none", "general"):
        return True
    if not worker:
        return False
    skills = get_worker_skills(worker)
    if "general" in skills:
        return True
    return req in skills


def get_machine_types(machine: Optional[Machine]) -> Set[str]:
    """Extracts normalized set of functional machine types for a piece of equipment."""
    if not machine or not machine.machine_type:
        return set()
    raw = machine.machine_type.strip()
    if raw.startswith("[") and raw.endswith("]"):
        import json
        try:
            items = json.loads(raw)
            if isinstance(items, list):
                return {str(i).strip().lower() for i in items if str(i).strip()}
        except Exception:
            pass
    return {s.strip().lower() for s in raw.split(",") if s.strip()}


def is_machine_compatible(machine: Optional[Machine], required_machine_type: Optional[str]) -> bool:
    """
    Determines if a machine is compatible with an operation requiring a specific machine type.
    Matching is deterministic and case-normalized.
    - If required_machine_type is empty, None, or 'none', no machine is required (compatible).
    - If required_machine_type is 'general', any machine is compatible.
    - If machine is 'general', it is compatible as general workshop equipment.
    - Otherwise, machine must match the required machine type.
    """
    if not required_machine_type or not required_machine_type.strip():
        return True
    req = required_machine_type.strip().lower()
    if req in ("none", "general"):
        return True
    if not machine:
        return False
    types = get_machine_types(machine)
    if "general" in types:
        return True
    return req in types


def check_worker_active_conflict(
    db: Session,
    user_id: Union[str, uuid.UUID],
    worker_id: Union[str, uuid.UUID],
    exclude_execution_id: Optional[Union[str, uuid.UUID]] = None,
    for_update: bool = True,
) -> Optional[OperationExecution]:
    """
    Checks if a worker is actively engaged in another operation (IN_PROGRESS or PAUSED).
    Returns the conflicting OperationExecution if found, or None if available.
    Uses row-level locking (with_for_update) to prevent concurrent double-booking.
    """
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
    if isinstance(worker_id, str):
        worker_id = uuid.UUID(worker_id)
    if isinstance(exclude_execution_id, str):
        exclude_execution_id = uuid.UUID(exclude_execution_id)

    stmt = (
        select(OperationExecution)
        .where(
            OperationExecution.user_id == user_id,
            OperationExecution.worker_id == worker_id,
            OperationExecution.status.in_([
                ExecutionStatus.IN_PROGRESS.value,
                ExecutionStatus.PAUSED.value,
            ]),
        )
    )
    if exclude_execution_id:
        stmt = stmt.where(OperationExecution.id != exclude_execution_id)
    if for_update:
        stmt = stmt.with_for_update()

    return db.scalar(stmt)


def check_machine_active_conflict(
    db: Session,
    user_id: Union[str, uuid.UUID],
    machine_id: Union[str, uuid.UUID],
    exclude_execution_id: Optional[Union[str, uuid.UUID]] = None,
    for_update: bool = True,
) -> Optional[OperationExecution]:
    """
    Checks if a machine is actively engaged in another operation (IN_PROGRESS or PAUSED).
    Returns the conflicting OperationExecution if found, or None if available.
    Uses row-level locking (with_for_update) to prevent concurrent double-booking.
    """
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
    if isinstance(machine_id, str):
        machine_id = uuid.UUID(machine_id)
    if isinstance(exclude_execution_id, str):
        exclude_execution_id = uuid.UUID(exclude_execution_id)

    stmt = (
        select(OperationExecution)
        .where(
            OperationExecution.user_id == user_id,
            OperationExecution.machine_id == machine_id,
            OperationExecution.status.in_([
                ExecutionStatus.IN_PROGRESS.value,
                ExecutionStatus.PAUSED.value,
            ]),
        )
    )
    if exclude_execution_id:
        stmt = stmt.where(OperationExecution.id != exclude_execution_id)
    if for_update:
        stmt = stmt.with_for_update()

    return db.scalar(stmt)


def serialize_execution_response(
    execution: OperationExecution,
    has_uncompleted_predecessors: bool = False,
) -> OperationExecutionResponse:
    """
    Serializes an OperationExecution ORM instance into its response schema,
    denormalizing step and resource information for operator inspection.
    Exposes planned vs actual execution resources (Phase J.3).
    """
    step = execution.production_step
    worker = execution.worker
    machine = execution.machine
    task = execution.scheduled_task
    current_status = execution.status

    task_worker_id = task.worker_id if task else None
    task_machine_id = task.machine_id if task else None
    task_worker_name = task.worker.name if (task and task.worker) else None
    task_machine_name = task.machine.name if (task and task.machine) else None

    worker_eligible = (
        is_worker_skill_eligible(worker, step.required_skill)
        if (worker and step and step.required_skill)
        else (True if (not step or not step.required_skill) else None)
    )
    machine_compatible = (
        is_machine_compatible(machine, step.required_machine_type)
        if (machine and step and step.required_machine_type)
        else (True if (not step or not step.required_machine_type) else None)
    )

    # Phase J.5 Quality Control & Rework Context
    latest_qc = execution.quality_checks[0] if (hasattr(execution, "quality_checks") and execution.quality_checks) else None
    latest_qc_result = latest_qc.result if latest_qc else None
    latest_defect_severity = latest_qc.defect_severity if latest_qc else None
    quality_gate_passed = (latest_qc_result == "PASS") if latest_qc_result else False

    return OperationExecutionResponse(
        id=execution.id,
        user_id=execution.user_id,
        production_order_id=execution.production_order_id,
        production_step_id=execution.production_step_id,
        scheduled_task_id=execution.scheduled_task_id,
        worker_id=execution.worker_id,
        machine_id=execution.machine_id,
        status=ExecutionStatus(current_status),
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
        actual_worker_id=execution.worker_id,
        actual_machine_id=execution.machine_id,
        planned_worker_id=task_worker_id,
        planned_machine_id=task_machine_id,
        planned_worker_name=task_worker_name,
        planned_machine_name=task_machine_name,
        worker_skill=worker.skill if worker else None,
        machine_type=machine.machine_type if machine else None,
        worker_eligible=worker_eligible,
        machine_compatible=machine_compatible,
        is_terminal=(current_status == ExecutionStatus.COMPLETED.value),
        can_start=(current_status == ExecutionStatus.READY.value),
        has_uncompleted_predecessors=has_uncompleted_predecessors,
        execution_type=getattr(execution, "execution_type", "normal") or "normal",
        rework_of_execution_id=getattr(execution, "rework_of_execution_id", None),
        attempt_number=getattr(execution, "attempt_number", 1) or 1,
        latest_qc_result=latest_qc_result,
        latest_defect_severity=latest_defect_severity,
        quality_gate_passed=quality_gate_passed,
    )


def build_order_execution_list_response(
    order: ProductionOrder,
    executions: List[OperationExecution],
) -> OperationExecutionListResponse:
    """
    Builds an OperationExecutionListResponse enriched with shop-floor workflow metrics.
    """
    total = len(executions)
    completed_count = sum(1 for e in executions if e.status == ExecutionStatus.COMPLETED.value)
    in_progress_count = sum(1 for e in executions if e.status == ExecutionStatus.IN_PROGRESS.value)
    ready_count = sum(1 for e in executions if e.status == ExecutionStatus.READY.value)
    pending_count = sum(1 for e in executions if e.status == ExecutionStatus.PENDING.value)
    blocked_count = sum(1 for e in executions if e.status == ExecutionStatus.BLOCKED.value)
    overall_progress_percent = round((completed_count / total * 100.0), 2) if total > 0 else 0.0

    # Determine active operation step number
    active_ex = (
        next((e for e in executions if e.status == ExecutionStatus.IN_PROGRESS.value), None)
        or next((e for e in executions if e.status == ExecutionStatus.READY.value), None)
        or next((e for e in executions if e.status == ExecutionStatus.BLOCKED.value), None)
        or (executions[-1] if completed_count == total and total > 0 else None)
    )
    current_step_number = active_ex.production_step.step_number if active_ex and active_ex.production_step else None

    items: List[OperationExecutionResponse] = []
    for e in executions:
        step_num = e.production_step.step_number if e.production_step else 0
        has_uncompleted = any(
            other.production_step.step_number < step_num and other.status != ExecutionStatus.COMPLETED.value
            for other in executions if other.production_step
        )
        items.append(serialize_execution_response(e, has_uncompleted_predecessors=has_uncompleted))

    return OperationExecutionListResponse(
        order_id=order.id,
        order_status=order.status,
        total=total,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        ready_count=ready_count,
        pending_count=pending_count,
        blocked_count=blocked_count,
        current_step_number=current_step_number,
        overall_progress_percent=overall_progress_percent,
        items=items,
    )


class ProductionExecutionService:
    """
    Foundational manufacturing execution service managing actual workshop
    operations, artisan transitions, timing reconciliation, order tracking,
    and automatic routing progression (Phase J.2).
    """

    @staticmethod
    def get_predecessors_for_execution(
        db: Session,
        execution: OperationExecution,
    ) -> List[OperationExecution]:
        """
        Returns all predecessor OperationExecution records for a given execution
        within its ProductionOrder routing.
        In the current sequential routing architecture:
        All operations with step_number < current execution's step_number are predecessors.
        """
        if not execution.production_step:
            execution.production_step = db.scalar(
                select(ProductionStep).where(ProductionStep.id == execution.production_step_id)
            )

        current_step_number = execution.production_step.step_number if execution.production_step else 0

        order_executions = list(
            db.scalars(
                select(OperationExecution)
                .options(joinedload(OperationExecution.production_step))
                .where(
                    OperationExecution.production_order_id == execution.production_order_id,
                    OperationExecution.user_id == execution.user_id,
                )
            ).all()
        )

        predecessors = [
            ex for ex in order_executions
            if ex.production_step and ex.production_step.step_number < current_step_number
        ]
        predecessors.sort(key=lambda ex: ex.production_step.step_number)
        return predecessors

    @staticmethod
    def validate_predecessors_completed(
        db: Session,
        execution: OperationExecution,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates that all predecessor operations for an execution are COMPLETED.
        Cross-references with the authoritative ProductionSpecification routing steps.
        Returns (True, None) if satisfied, or (False, error_message) if not.
        """
        if not execution.production_step:
            execution.production_step = db.scalar(
                select(ProductionStep).where(ProductionStep.id == execution.production_step_id)
            )

        current_step_number = execution.production_step.step_number if execution.production_step else 0

        # Load order with specification routing steps
        order = db.scalar(
            select(ProductionOrder)
            .options(joinedload(ProductionOrder.specification).selectinload(ProductionSpecification.steps))
            .where(ProductionOrder.id == execution.production_order_id)
        )

        if order and order.specification and order.specification.steps:
            required_predecessors = [
                s for s in order.specification.steps
                if s.step_number < current_step_number
            ]
            if required_predecessors:
                order_executions = list(
                    db.scalars(
                        select(OperationExecution)
                        .options(joinedload(OperationExecution.production_step))
                        .where(
                            OperationExecution.production_order_id == execution.production_order_id,
                            OperationExecution.user_id == execution.user_id,
                        )
                    ).all()
                )
                exec_by_step_id = {e.production_step_id: e for e in order_executions}

                for req_step in sorted(required_predecessors, key=lambda s: s.step_number):
                    pred_exec = exec_by_step_id.get(req_step.id)
                    if not pred_exec:
                        return False, f"Predecessor step #{req_step.step_number} ('{req_step.stage_name}') has no execution record and must be COMPLETED."
                    if pred_exec.status != ExecutionStatus.COMPLETED.value:
                        return False, f"Predecessor step #{req_step.step_number} ('{req_step.stage_name}') is currently in '{pred_exec.status}' state and must be COMPLETED."

                return True, None

        # Fallback if specification not directly resolvable
        predecessors = ProductionExecutionService.get_predecessors_for_execution(db, execution)
        for pred in predecessors:
            if pred.status != ExecutionStatus.COMPLETED.value:
                step_num = pred.production_step.step_number if pred.production_step else "?"
                stage = pred.production_step.stage_name if pred.production_step else "Unknown"
                return False, f"Predecessor step #{step_num} ('{stage}') is currently in '{pred.status}' state and must be COMPLETED."
        return True, None

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

        task_by_seq: Dict[int, ScheduledTask] = {
            t.sequence_order: t for t in scheduled_tasks
        }

        # 5. Build executions atomically
        executions_to_create: List[OperationExecution] = []
        for idx, step in enumerate(sorted_steps):
            initial_status = ExecutionStatus.READY.value if idx == 0 else ExecutionStatus.PENDING.value

            matched_task: Optional[ScheduledTask] = task_by_seq.get(step.step_number)
            if not matched_task and idx < len(scheduled_tasks):
                matched_task = scheduled_tasks[idx]

            planned_start = matched_task.start_time if matched_task else None
            planned_end = matched_task.end_time if matched_task else None
            if matched_task:
                planned_duration = matched_task.duration_hours
                assigned_worker_id = matched_task.worker_id
                assigned_machine_id = matched_task.machine_id
                matched_task_id = matched_task.id
            else:
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
                joinedload(OperationExecution.scheduled_task).joinedload(ScheduledTask.worker),
                joinedload(OperationExecution.scheduled_task).joinedload(ScheduledTask.machine),
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
    def get_order_execution_list_response(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
    ) -> OperationExecutionListResponse:
        """
        Retrieves all executions for an order enriched with workflow progress indicators.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        order = db.scalar(
            select(ProductionOrder).where(
                ProductionOrder.id == order_id,
                ProductionOrder.user_id == user_id,
            )
        )
        if not order:
            raise AppException("Production order not found.", code="ORDER_NOT_FOUND", status_code=404)

        executions = ProductionExecutionService.get_order_executions(db, user_id, order_id)
        return build_order_execution_list_response(order, executions)

    @staticmethod
    def get_execution_by_id(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
        for_update: bool = False,
    ) -> OperationExecution:
        """
        Retrieves a single operation execution with loaded relationships,
        enforcing multi-tenant isolation and optional row-level locking.
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
                joinedload(OperationExecution.scheduled_task).joinedload(ScheduledTask.worker),
                joinedload(OperationExecution.scheduled_task).joinedload(ScheduledTask.machine),
            )
            .where(
                OperationExecution.id == execution_id,
                OperationExecution.user_id == user_id,
            )
        )
        if for_update:
            stmt = stmt.with_for_update()

        execution = db.scalar(stmt)
        if not execution:
            raise AppException(
                "Operation execution not found.",
                code="EXECUTION_NOT_FOUND",
                status_code=404,
            )
        return execution

    @staticmethod
    def is_worker_available(
        db: Session,
        user_id: Union[str, uuid.UUID],
        worker_id: Union[str, uuid.UUID],
        exclude_execution_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> Tuple[bool, Optional[OperationExecution]]:
        """
        Determines if a worker is currently available to start an operation.
        A worker is unavailable if actively engaged in an operation with status IN_PROGRESS or PAUSED.
        Returns (True, None) if available, or (False, conflicting_execution) if busy.
        """
        conflict = check_worker_active_conflict(
            db=db,
            user_id=user_id,
            worker_id=worker_id,
            exclude_execution_id=exclude_execution_id,
            for_update=False,
        )
        if conflict:
            return False, conflict
        return True, None

    @staticmethod
    def is_machine_available(
        db: Session,
        user_id: Union[str, uuid.UUID],
        machine_id: Union[str, uuid.UUID],
        exclude_execution_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> Tuple[bool, Optional[OperationExecution]]:
        """
        Determines if a machine is currently available to start an operation.
        A machine is unavailable if actively utilized in an operation with status IN_PROGRESS or PAUSED.
        Returns (True, None) if available, or (False, conflicting_execution) if busy.
        """
        conflict = check_machine_active_conflict(
            db=db,
            user_id=user_id,
            machine_id=machine_id,
            exclude_execution_id=exclude_execution_id,
            for_update=False,
        )
        if conflict:
            return False, conflict
        return True, None

    @staticmethod
    def assign_worker(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
        worker_id: Union[str, uuid.UUID],
    ) -> OperationExecution:
        """
        Assigns an eligible worker to an operation execution.
        Validates:
        1. Multi-tenant ownership of execution.
        2. Execution state: rejects assignment to COMPLETED or reassignment while IN_PROGRESS / PAUSED.
        3. Multi-tenant ownership of worker (without exposing other tenant existence).
        4. Worker active presence/availability flag.
        5. Worker skill eligibility against ProductionStep required_skill.
        Atomically updates and commits worker_id.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(execution_id, str):
            execution_id = uuid.UUID(execution_id)
        if isinstance(worker_id, str):
            worker_id = uuid.UUID(worker_id)

        execution = ProductionExecutionService.get_execution_by_id(
            db=db,
            user_id=user_id,
            execution_id=execution_id,
            for_update=True,
        )

        # 1. State validation
        if execution.status == ExecutionStatus.COMPLETED.value:
            raise AppException(
                "Completed operation executions are immutable and cannot be assigned a worker.",
                code="EXECUTION_ALREADY_COMPLETED",
                status_code=409,
            )
        if execution.status in (ExecutionStatus.IN_PROGRESS.value, ExecutionStatus.PAUSED.value):
            raise AppException(
                f"Cannot reassign worker while operation is in '{execution.status}' state.",
                code="REASSIGNMENT_NOT_ALLOWED",
                status_code=409,
            )

        # 2. Worker ownership validation
        worker = db.scalar(
            select(Worker).where(Worker.id == worker_id, Worker.user_id == user_id)
        )
        if not worker:
            raise AppException(
                "Worker not found or belongs to another tenant.",
                code="WORKER_NOT_FOUND",
                status_code=404,
            )
        if not worker.is_available:
            raise AppException(
                f"Worker '{worker.name}' is currently marked unavailable.",
                code="WORKER_NOT_AVAILABLE",
                status_code=409,
            )

        # 3. Skill eligibility validation
        if not execution.production_step:
            execution.production_step = db.scalar(
                select(ProductionStep).where(ProductionStep.id == execution.production_step_id)
            )
        step = execution.production_step
        if step and step.required_skill:
            if not is_worker_skill_eligible(worker, step.required_skill):
                raise AppException(
                    f"Worker '{worker.name}' does not possess required skill '{step.required_skill}'. "
                    f"Worker skill: '{worker.skill}'.",
                    code="WORKER_INELIGIBLE_SKILL",
                    status_code=409,
                )

        execution.worker_id = worker.id
        execution.worker = worker

        try:
            db.commit()
            db.refresh(execution)
        except Exception:
            db.rollback()
            raise

        return execution

    @staticmethod
    def assign_machine(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
        machine_id: Union[str, uuid.UUID],
    ) -> OperationExecution:
        """
        Assigns compatible equipment to an operation execution.
        Validates:
        1. Multi-tenant ownership of execution.
        2. Execution state: rejects assignment to COMPLETED or reassignment while IN_PROGRESS / PAUSED.
        3. Multi-tenant ownership of machine (without exposing other tenant existence).
        4. Machine operational availability flag.
        5. Machine compatibility against ProductionStep required_machine_type.
        Atomically updates and commits machine_id.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(execution_id, str):
            execution_id = uuid.UUID(execution_id)
        if isinstance(machine_id, str):
            machine_id = uuid.UUID(machine_id)

        execution = ProductionExecutionService.get_execution_by_id(
            db=db,
            user_id=user_id,
            execution_id=execution_id,
            for_update=True,
        )

        # 1. State validation
        if execution.status == ExecutionStatus.COMPLETED.value:
            raise AppException(
                "Completed operation executions are immutable and cannot be assigned a machine.",
                code="EXECUTION_ALREADY_COMPLETED",
                status_code=409,
            )
        if execution.status in (ExecutionStatus.IN_PROGRESS.value, ExecutionStatus.PAUSED.value):
            raise AppException(
                f"Cannot reassign machine while operation is in '{execution.status}' state.",
                code="REASSIGNMENT_NOT_ALLOWED",
                status_code=409,
            )

        # 2. Machine ownership validation
        machine = db.scalar(
            select(Machine).where(Machine.id == machine_id, Machine.user_id == user_id)
        )
        if not machine:
            raise AppException(
                "Machine not found or belongs to another tenant.",
                code="MACHINE_NOT_FOUND",
                status_code=404,
            )
        if not machine.is_available:
            raise AppException(
                f"Machine '{machine.name}' is currently marked unavailable/offline.",
                code="MACHINE_NOT_AVAILABLE",
                status_code=409,
            )

        # 3. Machine compatibility validation
        if not execution.production_step:
            execution.production_step = db.scalar(
                select(ProductionStep).where(ProductionStep.id == execution.production_step_id)
            )
        step = execution.production_step
        if step and step.required_machine_type:
            if not is_machine_compatible(machine, step.required_machine_type):
                raise AppException(
                    f"Machine '{machine.name}' (type '{machine.machine_type}') is incompatible with "
                    f"required machine type '{step.required_machine_type}'.",
                    code="MACHINE_INCOMPATIBLE_TYPE",
                    status_code=409,
                )

        execution.machine_id = machine.id
        execution.machine = machine

        try:
            db.commit()
            db.refresh(execution)
        except Exception:
            db.rollback()
            raise

        return execution

    @staticmethod
    def transition_execution(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
        req: OperationExecutionTransitionRequest,
        validate_resources: Optional[bool] = None,
        _simulate_advancement_failure: bool = False,
    ) -> OperationExecution:
        """
        Executes a validated state transition on an OperationExecution.
        Updates shop-floor timestamps, calculates elapsed/pause durations,
        validates resource ownership and eligibility (Phase J.3),
        advances next sequential operation atomically (Phase J.2),
        and updates production order status atomically.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(execution_id, str):
            execution_id = uuid.UUID(execution_id)

        # 1. Load execution with tenant isolation and row-level lock
        execution = ProductionExecutionService.get_execution_by_id(
            db=db,
            user_id=user_id,
            execution_id=execution_id,
            for_update=True,
        )

        current_status = ExecutionStatus(execution.status)
        target_status = req.target_status
        now = datetime.now(timezone.utc)
        eff_validate_resources = validate_resources if validate_resources is not None else getattr(req, "validate_resources", None)

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

        # 4. Predecessor validation: an operation cannot become READY or IN_PROGRESS unless all predecessors are COMPLETED
        if target_status in (ExecutionStatus.READY, ExecutionStatus.IN_PROGRESS):
            is_valid, err_msg = ProductionExecutionService.validate_predecessors_completed(db, execution)
            if not is_valid:
                raise AppException(
                    f"Cannot transition operation to '{target_status.value}': {err_msg}",
                    code="PREDECESSOR_NOT_COMPLETED",
                    status_code=409,
                )

        # 5. Reassignment validation for active/completed operations (Phase J.3)
        if current_status in (ExecutionStatus.IN_PROGRESS, ExecutionStatus.PAUSED, ExecutionStatus.COMPLETED):
            if req.worker_id is not None and req.worker_id != execution.worker_id:
                raise AppException(
                    f"Cannot reassign worker while operation is in '{current_status.value}' state.",
                    code="REASSIGNMENT_NOT_ALLOWED",
                    status_code=409,
                )
            if req.machine_id is not None and req.machine_id != execution.machine_id:
                raise AppException(
                    f"Cannot reassign machine while operation is in '{current_status.value}' state.",
                    code="REASSIGNMENT_NOT_ALLOWED",
                    status_code=409,
                )

        # Optional resource assignment during transition (valid in READY, PENDING, BLOCKED)
        if req.worker_id is not None and current_status not in (ExecutionStatus.IN_PROGRESS, ExecutionStatus.PAUSED, ExecutionStatus.COMPLETED):
            worker = db.scalar(
                select(Worker).where(Worker.id == req.worker_id, Worker.user_id == user_id)
            )
            if not worker:
                raise AppException("Worker not found or belongs to another tenant.", code="WORKER_NOT_FOUND", status_code=404)
            if not worker.is_available:
                raise AppException(f"Worker '{worker.name}' is currently unavailable.", code="WORKER_NOT_AVAILABLE", status_code=409)
            if not execution.production_step:
                execution.production_step = db.scalar(
                    select(ProductionStep).where(ProductionStep.id == execution.production_step_id)
                )
            if execution.production_step and execution.production_step.required_skill:
                if not is_worker_skill_eligible(worker, execution.production_step.required_skill):
                    raise AppException(
                        f"Worker '{worker.name}' lacks required skill '{execution.production_step.required_skill}'.",
                        code="WORKER_INELIGIBLE_SKILL",
                        status_code=409,
                    )
            execution.worker_id = worker.id
            execution.worker = worker

        if req.machine_id is not None and current_status not in (ExecutionStatus.IN_PROGRESS, ExecutionStatus.PAUSED, ExecutionStatus.COMPLETED):
            machine = db.scalar(
                select(Machine).where(Machine.id == req.machine_id, Machine.user_id == user_id)
            )
            if not machine:
                raise AppException("Machine not found or belongs to another tenant.", code="MACHINE_NOT_FOUND", status_code=404)
            if not machine.is_available:
                raise AppException(f"Machine '{machine.name}' is currently unavailable.", code="MACHINE_NOT_AVAILABLE", status_code=409)
            if not execution.production_step:
                execution.production_step = db.scalar(
                    select(ProductionStep).where(ProductionStep.id == execution.production_step_id)
                )
            if execution.production_step and execution.production_step.required_machine_type:
                if not is_machine_compatible(machine, execution.production_step.required_machine_type):
                    raise AppException(
                        f"Machine '{machine.name}' is incompatible with required type '{execution.production_step.required_machine_type}'.",
                        code="MACHINE_INCOMPATIBLE_TYPE",
                        status_code=409,
                    )
            execution.machine_id = machine.id
            execution.machine = machine

        # 5b. Start Requirements & Resource Conflict validation (READY -> IN_PROGRESS)
        if target_status == ExecutionStatus.IN_PROGRESS:
            if not execution.production_step:
                execution.production_step = db.scalar(
                    select(ProductionStep).where(ProductionStep.id == execution.production_step_id)
                )
            step = execution.production_step

            # Check if tenant has workshop resources registered
            has_tenant_workers = db.scalar(select(Worker.id).where(Worker.user_id == user_id).limit(1)) is not None
            has_tenant_machines = db.scalar(select(Machine.id).where(Machine.user_id == user_id).limit(1)) is not None
            should_validate = (
                (eff_validate_resources is True)
                or (eff_validate_resources is None and (has_tenant_workers or has_tenant_machines))
            )

            # Worker validation
            worker_required = bool(
                step
                and step.required_skill
                and step.required_skill.strip()
                and step.required_skill.strip().lower() != "none"
            )
            if worker_required and should_validate:
                if not execution.worker_id:
                    raise AppException(
                        f"Operation step #{step.step_number} ('{step.stage_name}') requires an artisan "
                        f"with skill '{step.required_skill}', but no worker is assigned.",
                        code="MISSING_REQUIRED_WORKER",
                        status_code=409,
                    )

            if execution.worker_id:
                if not execution.worker:
                    execution.worker = db.scalar(select(Worker).where(Worker.id == execution.worker_id))
                if worker_required and step and not is_worker_skill_eligible(execution.worker, step.required_skill):
                    raise AppException(
                        f"Assigned worker '{execution.worker.name}' lacks required skill '{step.required_skill}'.",
                        code="WORKER_INELIGIBLE_SKILL",
                        status_code=409,
                    )
                # Worker availability / conflict check
                conflict_w = check_worker_active_conflict(
                    db=db,
                    user_id=user_id,
                    worker_id=execution.worker_id,
                    exclude_execution_id=execution.id,
                    for_update=True,
                )
                if conflict_w:
                    raise AppException(
                        f"Worker '{execution.worker.name if execution.worker else execution.worker_id}' is currently active on "
                        f"another operation (Execution ID: {conflict_w.id}, status: '{conflict_w.status}').",
                        code="WORKER_RESOURCE_CONFLICT",
                        status_code=409,
                    )

            # Machine validation
            machine_required = bool(
                step
                and step.required_machine_type
                and step.required_machine_type.strip()
                and step.required_machine_type.strip().lower() != "none"
            )
            if machine_required and should_validate:
                if not execution.machine_id:
                    raise AppException(
                        f"Operation step #{step.step_number} ('{step.stage_name}') requires equipment "
                        f"of type '{step.required_machine_type}', but no machine is assigned.",
                        code="MISSING_REQUIRED_MACHINE",
                        status_code=409,
                    )

            if execution.machine_id:
                if not execution.machine:
                    execution.machine = db.scalar(select(Machine).where(Machine.id == execution.machine_id))
                if machine_required and step and not is_machine_compatible(execution.machine, step.required_machine_type):
                    raise AppException(
                        f"Assigned machine '{execution.machine.name}' is incompatible with required type '{step.required_machine_type}'.",
                        code="MACHINE_INCOMPATIBLE_TYPE",
                        status_code=409,
                    )
                # Machine availability / conflict check
                conflict_m = check_machine_active_conflict(
                    db=db,
                    user_id=user_id,
                    machine_id=execution.machine_id,
                    exclude_execution_id=execution.id,
                    for_update=True,
                )
                if conflict_m:
                    raise AppException(
                        f"Machine '{execution.machine.name if execution.machine else execution.machine_id}' is currently in use on "
                        f"another operation (Execution ID: {conflict_m.id}, status: '{conflict_m.status}').",
                        code="MACHINE_RESOURCE_CONFLICT",
                        status_code=409,
                    )

        # 6. Apply timing logic according to the transition
        if current_status == ExecutionStatus.READY and target_status == ExecutionStatus.IN_PROGRESS:
            if not execution.actual_start_time:
                execution.actual_start_time = now

        elif current_status == ExecutionStatus.IN_PROGRESS and target_status == ExecutionStatus.PAUSED:
            execution.last_paused_at = now

        elif current_status == ExecutionStatus.PAUSED and target_status == ExecutionStatus.IN_PROGRESS:
            last_p = _ensure_utc(execution.last_paused_at)
            if last_p:
                pause_delta_hours = (now - last_p).total_seconds() / 3600.0
                execution.pause_duration_hours += max(0.0, pause_delta_hours)
                execution.last_paused_at = None

        elif current_status == ExecutionStatus.IN_PROGRESS and target_status == ExecutionStatus.COMPLETED:
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
            if current_status == ExecutionStatus.IN_PROGRESS:
                execution.last_paused_at = now

        elif current_status == ExecutionStatus.BLOCKED and target_status == ExecutionStatus.READY:
            last_p = _ensure_utc(execution.last_paused_at)
            if last_p:
                pause_delta_hours = (now - last_p).total_seconds() / 3600.0
                execution.pause_duration_hours += max(0.0, pause_delta_hours)
                execution.last_paused_at = None

        # 7. Apply status and notes
        execution.status = target_status.value
        if req.operator_notes is not None:
            if execution.operator_notes:
                execution.operator_notes = f"{execution.operator_notes}\n[{now.strftime('%Y-%m-%d %H:%M:%S UTC')}] {req.operator_notes}"
            else:
                execution.operator_notes = req.operator_notes

        # 8. Automatic Routing Progression & Order Status reconciliation (Phase J.2)
        if target_status == ExecutionStatus.COMPLETED:
            # Query all executions for this order to find the immediate next sequential step
            order_executions = list(
                db.scalars(
                    select(OperationExecution)
                    .options(joinedload(OperationExecution.production_step))
                    .where(
                        OperationExecution.production_order_id == execution.production_order_id,
                        OperationExecution.user_id == user_id,
                    )
                    .with_for_update()
                ).all()
            )
            order_executions.sort(key=lambda e: (e.production_step.step_number if e.production_step else 0))

            curr_step_num = execution.production_step.step_number if execution.production_step else 0

            # Find subsequent execution(s)
            subsequent = [
                e for e in order_executions
                if e.production_step and e.production_step.step_number > curr_step_num
            ]

            if subsequent:
                next_ex = subsequent[0]
                # Check if all predecessors of next_ex are completed (including current execution)
                can_advance = True
                for e in order_executions:
                    if e.production_step and e.production_step.step_number < next_ex.production_step.step_number:
                        if e.id == execution.id:
                            continue  # Current execution is already marked completed above
                        if e.status != ExecutionStatus.COMPLETED.value:
                            can_advance = False
                            break

                if can_advance and next_ex.status == ExecutionStatus.PENDING.value:
                    # Test simulation hook for atomic rollback testing
                    if _simulate_advancement_failure or getattr(req, "_simulate_advancement_failure", False):
                        raise RuntimeError("Simulated failure during next-step advancement.")

                    next_ex.status = ExecutionStatus.READY.value
                    stage_name = execution.production_step.stage_name if execution.production_step else ""
                    auto_note = (
                        f"[{now.strftime('%Y-%m-%d %H:%M:%S UTC')}] Automatically advanced to READY "
                        f"upon completion of step #{curr_step_num} ('{stage_name}')."
                    )
                    next_ex.operator_notes = (
                        f"{next_ex.operator_notes}\n{auto_note}" if next_ex.operator_notes else auto_note
                    )

            # Reconcile parent ProductionOrder status
            order = db.scalar(
                select(ProductionOrder)
                .where(ProductionOrder.id == execution.production_order_id, ProductionOrder.user_id == user_id)
                .with_for_update()
            )
            if order:
                all_completed = all(e.status == ExecutionStatus.COMPLETED.value for e in order_executions)
                if all_completed:
                    # Phase J.5 Quality Control Completion Gate:
                    # If quality checks exist on this order, verify 100% PASS before marking COMPLETED
                    qc_exists = db.scalar(
                        select(func.count(QualityCheck.id))
                        .where(
                            QualityCheck.production_order_id == order.id,
                            QualityCheck.user_id == user_id,
                        )
                    ) or 0
                    if qc_exists > 0:
                        metrics = ProductionExecutionService.calculate_order_quality_metrics(
                            db, user_id, order.id, order_executions
                        )
                        if metrics["quality_gate_passed"]:
                            order.status = "completed"
                        else:
                            order.status = "in_progress"
                    else:
                        order.status = "completed"
                elif order.status == "pending":
                    order.status = "in_progress"

        elif target_status == ExecutionStatus.IN_PROGRESS:
            order = db.scalar(
                select(ProductionOrder)
                .where(ProductionOrder.id == execution.production_order_id, ProductionOrder.user_id == user_id)
                .with_for_update()
            )
            if order and order.status == "pending":
                order.status = "in_progress"

        # 9. Atomically commit all changes (both current and next execution)
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
        Manually creates an OperationExecution record with strict linkage & predecessor validation:
        - Verifies that the ProductionStep belongs to the ProductionSpecification of the ProductionOrder.
        - Verifies that any referenced ScheduledTask belongs to the same order and user.
        - Verifies that any referenced Worker or Machine belongs to the user.
        - Rejects duplicate execution creation for the same order and step.
        - Enforces predecessor validation: starts READY only if predecessors are complete, otherwise PENDING.
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

        # 2. Check for duplicate execution
        existing = db.scalar(
            select(OperationExecution).where(
                OperationExecution.production_order_id == order.id,
                OperationExecution.production_step_id == create_in.production_step_id,
            )
        )
        if existing:
            raise AppException(
                "An execution record already exists for this production order and step.",
                code="EXECUTION_ALREADY_EXISTS",
                status_code=409,
            )

        # 3. Validate ProductionStep belongs to this order's specification
        valid_step_ids = {s.id for s in order.specification.steps}
        if create_in.production_step_id not in valid_step_ids:
            raise AppException(
                "ProductionStep does not belong to the specification associated with this production order.",
                code="INVALID_STEP_ORDER_LINKAGE",
                status_code=400,
            )

        step = next(s for s in order.specification.steps if s.id == create_in.production_step_id)

        # 4. Validate ScheduledTask linkage if provided
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

        # 5. Validate Worker & Machine ownership and compatibility
        if create_in.worker_id is not None:
            worker = db.scalar(
                select(Worker).where(Worker.id == create_in.worker_id, Worker.user_id == user_id)
            )
            if not worker:
                raise AppException("Worker not found or belongs to another tenant.", code="WORKER_NOT_FOUND", status_code=404)
            if not worker.is_available:
                raise AppException(f"Worker '{worker.name}' is currently unavailable.", code="WORKER_NOT_AVAILABLE", status_code=409)
            if step and step.required_skill:
                if not is_worker_skill_eligible(worker, step.required_skill):
                    raise AppException(
                        f"Worker '{worker.name}' lacks required skill '{step.required_skill}'.",
                        code="WORKER_INELIGIBLE_SKILL",
                        status_code=409,
                    )

        if create_in.machine_id is not None:
            machine = db.scalar(
                select(Machine).where(Machine.id == create_in.machine_id, Machine.user_id == user_id)
            )
            if not machine:
                raise AppException("Machine not found or belongs to another tenant.", code="MACHINE_NOT_FOUND", status_code=404)
            if not machine.is_available:
                raise AppException(f"Machine '{machine.name}' is currently unavailable.", code="MACHINE_NOT_AVAILABLE", status_code=409)
            if step and step.required_machine_type:
                if not is_machine_compatible(machine, step.required_machine_type):
                    raise AppException(
                        f"Machine '{machine.name}' is incompatible with required type '{step.required_machine_type}'.",
                        code="MACHINE_INCOMPATIBLE_TYPE",
                        status_code=409,
                    )

        # 6. Predecessor validation: determine initial status (READY vs PENDING)
        predecessor_steps = [
            s for s in order.specification.steps if s.step_number < step.step_number
        ]
        if predecessor_steps:
            pred_step_ids = {s.id for s in predecessor_steps}
            completed_preds = set(
                db.scalars(
                    select(OperationExecution.production_step_id).where(
                        OperationExecution.production_order_id == order.id,
                        OperationExecution.production_step_id.in_(pred_step_ids),
                        OperationExecution.status == ExecutionStatus.COMPLETED.value,
                    )
                ).all()
            )
            if len(completed_preds) < len(predecessor_steps):
                initial_status = ExecutionStatus.PENDING.value
            else:
                initial_status = ExecutionStatus.READY.value
        else:
            initial_status = ExecutionStatus.READY.value

        # 7. Timing defaults
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

    # =========================================================================
    # Phase J.4: Material Consumption & Wastage Tracking
    # =========================================================================

    @staticmethod
    def record_material_consumption(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
        payload: MaterialConsumptionCreate,
    ) -> MaterialConsumption:
        """
        Records actual material consumption and wastage against an active or completed
        shop-floor operation execution. Enforces tenant ownership, execution state rules
        (IN_PROGRESS or COMPLETED only), quantity constraints, and authoritative
        specification item alignment.

        Traceability chain:
        ProductionSpecification -> ProductionOrder -> OperationExecution -> MaterialConsumption
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(execution_id, str):
            execution_id = uuid.UUID(execution_id)

        # 1. Tenant-scoped execution lookup
        execution = db.scalar(
            select(OperationExecution)
            .where(
                OperationExecution.id == execution_id,
                OperationExecution.user_id == user_id,
            )
        )
        if not execution:
            raise AppException(
                "Operation execution not found.",
                code="EXECUTION_NOT_FOUND",
                status_code=404,
            )

        # 2. Execution state validation (only IN_PROGRESS or COMPLETED represent real work)
        if execution.status not in (ExecutionStatus.IN_PROGRESS.value, ExecutionStatus.COMPLETED.value):
            raise AppException(
                f"Cannot record material consumption for execution in '{execution.status}' state. "
                "Consumption can only be recorded when execution is IN_PROGRESS or COMPLETED.",
                code="INVALID_EXECUTION_STATE",
                status_code=400,
            )

        # 3. Tenant-scoped order lookup & linkage validation
        order = db.scalar(
            select(ProductionOrder)
            .where(
                ProductionOrder.id == execution.production_order_id,
                ProductionOrder.user_id == user_id,
            )
        )
        if not order:
            raise AppException(
                "Production order not found for this execution.",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        # 4. Authoritative specification item linkage & validation
        spec_material: Optional[ProductionMaterial] = None
        spec_gemstone: Optional[ProductionGemstone] = None

        if payload.specification_material_id:
            # Query material strictly scoped to current tenant
            spec_material = db.scalar(
                select(ProductionMaterial)
                .join(
                    ProductionSpecification,
                    ProductionMaterial.specification_id == ProductionSpecification.id,
                )
                .where(
                    ProductionMaterial.id == payload.specification_material_id,
                    ProductionSpecification.user_id == user_id,
                )
            )
            if not spec_material:
                raise AppException(
                    "Specification material not found.",
                    code="SPECIFICATION_MATERIAL_NOT_FOUND",
                    status_code=404,
                )

            # Prevent cross-order / cross-specification mismatch
            if not order.specification_id or spec_material.specification_id != order.specification_id:
                raise AppException(
                    "Specification material does not belong to the production order's specification.",
                    code="SPECIFICATION_MATERIAL_MISMATCH",
                    status_code=400,
                )

        if payload.specification_gemstone_id:
            # Query gemstone strictly scoped to current tenant
            spec_gemstone = db.scalar(
                select(ProductionGemstone)
                .join(
                    ProductionSpecification,
                    ProductionGemstone.specification_id == ProductionSpecification.id,
                )
                .where(
                    ProductionGemstone.id == payload.specification_gemstone_id,
                    ProductionSpecification.user_id == user_id,
                )
            )
            if not spec_gemstone:
                raise AppException(
                    "Specification gemstone not found.",
                    code="SPECIFICATION_GEMSTONE_NOT_FOUND",
                    status_code=404,
                )

            # Prevent cross-order / cross-specification mismatch
            if not order.specification_id or spec_gemstone.specification_id != order.specification_id:
                raise AppException(
                    "Specification gemstone does not belong to the production order's specification.",
                    code="SPECIFICATION_GEMSTONE_MISMATCH",
                    status_code=400,
                )

        # 5. Derive identity / attributes
        resolved_type = payload.material_type
        resolved_name = payload.material_name
        resolved_unit = payload.unit or "g"
        resolved_planned = payload.planned_quantity

        if spec_material:
            if not resolved_type:
                resolved_type = "METAL"
            if not resolved_name:
                color_str = f" {spec_material.metal_color}" if spec_material.metal_color else ""
                resolved_name = f"{spec_material.metal_purity}{color_str} {spec_material.metal_type}".strip()
            if not resolved_unit:
                resolved_unit = "g"
            if resolved_planned == 0.0 and spec_material.estimated_weight_grams is not None:
                resolved_planned = float(spec_material.estimated_weight_grams)

        elif spec_gemstone:
            if not resolved_type:
                resolved_type = "GEMSTONE"
            if not resolved_name:
                shape_str = f" ({spec_gemstone.cut_shape})" if spec_gemstone.cut_shape else ""
                resolved_name = f"{spec_gemstone.gemstone_type}{shape_str}".strip()
            if not resolved_unit:
                resolved_unit = "pcs"
            if resolved_planned == 0.0:
                if spec_gemstone.stone_count is not None:
                    resolved_planned = float(spec_gemstone.stone_count)
                elif spec_gemstone.estimated_carat_weight is not None:
                    resolved_planned = float(spec_gemstone.estimated_carat_weight)

        resolved_type = (resolved_type or "METAL").strip().upper()

        # 6. Strict quantity and wastage validation
        if payload.actual_quantity < 0.0:
            raise AppException(
                "Actual quantity must be non-negative.",
                code="INVALID_QUANTITY",
                status_code=400,
            )
        if payload.wastage_quantity < 0.0:
            raise AppException(
                "Wastage quantity must be non-negative.",
                code="INVALID_QUANTITY",
                status_code=400,
            )
        if resolved_planned < 0.0:
            raise AppException(
                "Planned quantity must be non-negative.",
                code="INVALID_QUANTITY",
                status_code=400,
            )
        if payload.wastage_quantity > payload.actual_quantity:
            raise AppException(
                "Wastage quantity cannot exceed actual quantity.",
                code="INVALID_QUANTITY",
                status_code=400,
            )

        # 7. Atomic persistence (Append-only actual manufacturing history)
        consumption = MaterialConsumption(
            id=uuid.uuid4(),
            user_id=user_id,
            production_order_id=order.id,
            operation_execution_id=execution.id,
            specification_material_id=spec_material.id if spec_material else None,
            specification_gemstone_id=spec_gemstone.id if spec_gemstone else None,
            material_type=resolved_type,
            material_name=resolved_name or "Unknown Material",
            unit=resolved_unit,
            planned_quantity=resolved_planned,
            actual_quantity=payload.actual_quantity,
            wastage_quantity=payload.wastage_quantity,
            wastage_reason=payload.wastage_reason,
            notes=payload.notes,
        )

        try:
            db.add(consumption)
            db.commit()
            db.refresh(consumption)
        except Exception:
            db.rollback()
            raise

        return consumption

    @staticmethod
    def get_execution_material_consumptions(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
    ) -> List[MaterialConsumption]:
        """
        Retrieves all actual material consumption records for an operation execution.
        Enforces tenant isolation.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(execution_id, str):
            execution_id = uuid.UUID(execution_id)

        execution = db.scalar(
            select(OperationExecution)
            .where(
                OperationExecution.id == execution_id,
                OperationExecution.user_id == user_id,
            )
        )
        if not execution:
            raise AppException(
                "Operation execution not found.",
                code="EXECUTION_NOT_FOUND",
                status_code=404,
            )

        return list(
            db.scalars(
                select(MaterialConsumption)
                .where(
                    MaterialConsumption.operation_execution_id == execution_id,
                    MaterialConsumption.user_id == user_id,
                )
                .order_by(MaterialConsumption.created_at.asc())
            ).all()
        )

    @staticmethod
    def get_order_material_consumptions(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
    ) -> List[MaterialConsumption]:
        """
        Retrieves all actual material consumption records for a production order.
        Enforces tenant isolation.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        order = db.scalar(
            select(ProductionOrder)
            .where(
                ProductionOrder.id == order_id,
                ProductionOrder.user_id == user_id,
            )
        )
        if not order:
            raise AppException(
                "Production order not found.",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        return list(
            db.scalars(
                select(MaterialConsumption)
                .where(
                    MaterialConsumption.production_order_id == order_id,
                    MaterialConsumption.user_id == user_id,
                )
                .order_by(MaterialConsumption.created_at.asc())
            ).all()
        )

    @staticmethod
    def get_order_material_summary(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
    ) -> OrderMaterialSummaryResponse:
        """
        Computes concise planned vs actual vs wastage summary for a production order,
        grouped by material category, name, and unit.
        Enforces multi-tenant isolation.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        order = db.scalar(
            select(ProductionOrder)
            .where(
                ProductionOrder.id == order_id,
                ProductionOrder.user_id == user_id,
            )
        )
        if not order:
            raise AppException(
                "Production order not found.",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        consumptions = list(
            db.scalars(
                select(MaterialConsumption)
                .where(
                    MaterialConsumption.production_order_id == order_id,
                    MaterialConsumption.user_id == user_id,
                )
                .order_by(MaterialConsumption.created_at.asc())
            ).all()
        )

        groups: Dict[Tuple[str, str, str], Dict[str, float]] = {}
        for c in consumptions:
            key = (c.material_type, c.material_name, c.unit)
            if key not in groups:
                groups[key] = {
                    "planned": 0.0,
                    "actual": 0.0,
                    "wastage": 0.0,
                }
            groups[key]["planned"] += c.planned_quantity
            groups[key]["actual"] += c.actual_quantity
            groups[key]["wastage"] += c.wastage_quantity

        items: List[MaterialSummaryItem] = []
        for (m_type, m_name, m_unit), vals in groups.items():
            actual = round(vals["actual"], 4)
            wastage = round(vals["wastage"], 4)
            planned = round(vals["planned"], 4)
            net = round(actual - wastage, 4)
            items.append(
                MaterialSummaryItem(
                    material_type=m_type,
                    material_name=m_name,
                    unit=m_unit,
                    planned_quantity=planned,
                    actual_quantity=actual,
                    wastage_quantity=wastage,
                    net_consumed_quantity=net,
                )
            )

        total_planned = round(sum(i.planned_quantity for i in items), 4)
        total_actual = round(sum(i.actual_quantity for i in items), 4)
        total_wastage = round(sum(i.wastage_quantity for i in items), 4)
        total_net = round(total_actual - total_wastage, 4)

        return OrderMaterialSummaryResponse(
            order_id=order.id,
            total_planned_quantity=total_planned,
            total_actual_quantity=total_actual,
            total_wastage_quantity=total_wastage,
            total_net_quantity=total_net,
            items=items,
        )

    # =========================================================================
    # Phase J.5: Quality Control & Controlled Rework Methods
    # =========================================================================

    @staticmethod
    def calculate_order_quality_metrics(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
        executions: Optional[List[OperationExecution]] = None,
    ) -> Dict[str, any]:
        """
        Calculates authoritative quality gate metrics for a production order.
        Groups execution history by routing step to evaluate the latest attempt's latest QC result.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        if executions is None:
            executions = list(
                db.scalars(
                    select(OperationExecution)
                    .where(
                        OperationExecution.production_order_id == order_id,
                        OperationExecution.user_id == user_id,
                    )
                    .options(
                        joinedload(OperationExecution.production_step),
                        selectinload(OperationExecution.quality_checks),
                    )
                    .order_by(
                        OperationExecution.attempt_number.asc(),
                        OperationExecution.created_at.asc(),
                    )
                ).all()
            )

        # Group executions by production_step_id
        step_executions: Dict[uuid.UUID, List[OperationExecution]] = {}
        for ex in executions:
            s_id = ex.production_step_id
            if s_id not in step_executions:
                step_executions[s_id] = []
            step_executions[s_id].append(ex)

        total_operations = len(step_executions)
        completed_operations = 0
        passed_count = 0
        failed_count = 0
        rework_count = 0
        pending_qc_count = 0
        total_checks = 0

        items: List[ExecutionQualitySummaryItem] = []

        for step_id, ex_list in step_executions.items():
            # Latest execution attempt for this step
            latest_ex = max(ex_list, key=lambda e: (getattr(e, "attempt_number", 1) or 1))
            is_completed = (latest_ex.status == ExecutionStatus.COMPLETED.value)
            if is_completed:
                completed_operations += 1

            # Checks for this latest attempt (ordered by checked_at desc)
            checks = latest_ex.quality_checks if (hasattr(latest_ex, "quality_checks") and latest_ex.quality_checks) else []
            if not checks and latest_ex.id:
                checks = list(
                    db.scalars(
                        select(QualityCheck)
                        .where(QualityCheck.operation_execution_id == latest_ex.id)
                        .order_by(QualityCheck.checked_at.desc(), QualityCheck.created_at.desc())
                    ).all()
                )
            total_checks += len(checks)

            latest_qc = checks[0] if checks else None
            latest_res = latest_qc.result.upper() if latest_qc else None
            latest_sev = latest_qc.defect_severity if latest_qc else None

            has_passed = (latest_res == "PASS")
            if latest_res == "PASS":
                passed_count += 1
            elif latest_res == "FAIL":
                failed_count += 1
            elif latest_res == "REWORK":
                rework_count += 1
            elif is_completed:
                pending_qc_count += 1

            step = latest_ex.production_step
            items.append(
                ExecutionQualitySummaryItem(
                    execution_id=latest_ex.id,
                    step_id=step_id,
                    step_number=step.step_number if step else None,
                    stage_name=step.stage_name if step else None,
                    execution_type=latest_ex.execution_type,
                    attempt_number=latest_ex.attempt_number,
                    execution_status=latest_ex.status,
                    latest_qc_result=latest_res,
                    latest_defect_severity=latest_sev,
                    total_checks=len(checks),
                    has_passed=has_passed,
                )
            )

        # Sort items by step_number
        items.sort(key=lambda x: (x.step_number or 0))

        # Quality gate passes ONLY IF all operations are completed and all latest attempts have PASS
        quality_gate_passed = (
            total_operations > 0
            and completed_operations == total_operations
            and passed_count == total_operations
            and failed_count == 0
            and rework_count == 0
            and pending_qc_count == 0
        )

        return {
            "order_id": order_id,
            "total_operations": total_operations,
            "completed_operations": completed_operations,
            "passed": passed_count,
            "failed": failed_count,
            "rework": rework_count,
            "pending_quality_checks": pending_qc_count,
            "total_checks": total_checks,
            "quality_gate_passed": quality_gate_passed,
            "items": items,
        }

    @staticmethod
    def record_quality_check(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
        payload: QualityCheckCreate,
    ) -> QualityCheckResponse:
        """
        Records an append-only quality inspection result against an OperationExecution.
        Validates tenant ownership, completed execution state, and specification linkage.
        Automatically reconciles parent ProductionOrder completion status based on quality gate.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(execution_id, str):
            execution_id = uuid.UUID(execution_id)

        # 1. Fetch execution with lock
        execution = db.scalar(
            select(OperationExecution)
            .where(
                OperationExecution.id == execution_id,
                OperationExecution.user_id == user_id,
            )
            .options(
                joinedload(OperationExecution.production_step),
                joinedload(OperationExecution.production_order),
            )
            .with_for_update()
        )
        if not execution:
            raise AppException(
                "Operation execution not found.",
                code="EXECUTION_NOT_FOUND",
                status_code=404,
            )

        # 2. Enforce execution state: must be COMPLETED
        if execution.status != ExecutionStatus.COMPLETED.value:
            raise AppException(
                f"Quality inspection can only be recorded for COMPLETED operations (current status: '{execution.status}').",
                code="INVALID_EXECUTION_STATE",
                status_code=409,
            )

        # 3. Fetch and lock order
        order = db.scalar(
            select(ProductionOrder)
            .where(
                ProductionOrder.id == execution.production_order_id,
                ProductionOrder.user_id == user_id,
            )
            .with_for_update()
        )
        if not order:
            raise AppException(
                "Production order not found.",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        # 4. Verify step
        step = execution.production_step
        if not step or step.id != execution.production_step_id:
            step = db.scalar(
                select(ProductionStep)
                .where(ProductionStep.id == execution.production_step_id)
            )
        if not step:
            raise AppException(
                "Production step not found.",
                code="STEP_NOT_FOUND",
                status_code=404,
            )

        # 5. Create append-only QualityCheck record
        norm_result = payload.result.value.upper()
        norm_severity = payload.defect_severity.value.upper()
        now = datetime.now(timezone.utc)

        qc = QualityCheck(
            id=uuid.uuid4(),
            user_id=user_id,
            production_order_id=order.id,
            operation_execution_id=execution.id,
            production_step_id=step.id,
            result=norm_result,
            defect_severity=norm_severity,
            defect_type=payload.defect_type.strip() if payload.defect_type else None,
            notes=payload.notes,
            checked_by=payload.checked_by.strip() if payload.checked_by else None,
            checked_at=now,
        )
        db.add(qc)
        db.flush()

        # 6. Reconcile parent ProductionOrder status based on quality gate
        metrics = ProductionExecutionService.calculate_order_quality_metrics(
            db, user_id, order.id
        )
        if metrics["quality_gate_passed"]:
            order.status = "completed"
        else:
            if order.status == "completed":
                order.status = "in_progress"

        try:
            db.commit()
            db.refresh(qc)
        except Exception:
            db.rollback()
            raise

        return QualityCheckResponse(
            id=qc.id,
            user_id=qc.user_id,
            production_order_id=qc.production_order_id,
            operation_execution_id=qc.operation_execution_id,
            production_step_id=qc.production_step_id,
            result=qc.result,
            defect_severity=qc.defect_severity,
            defect_type=qc.defect_type,
            notes=qc.notes,
            checked_by=qc.checked_by,
            checked_at=qc.checked_at,
            created_at=qc.created_at,
            updated_at=qc.updated_at,
            step_number=step.step_number if step else None,
            stage_name=step.stage_name if step else None,
            quality_checkpoint=step.quality_checkpoint if step else None,
        )

    @staticmethod
    def get_execution_quality_checks(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
    ) -> List[QualityCheckResponse]:
        """
        Retrieves complete chronological quality check history for an operation execution,
        ordered latest first (descending).
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(execution_id, str):
            execution_id = uuid.UUID(execution_id)

        execution = db.scalar(
            select(OperationExecution)
            .where(
                OperationExecution.id == execution_id,
                OperationExecution.user_id == user_id,
            )
            .options(joinedload(OperationExecution.production_step))
        )
        if not execution:
            raise AppException(
                "Operation execution not found.",
                code="EXECUTION_NOT_FOUND",
                status_code=404,
            )

        step = execution.production_step
        records = list(
            db.scalars(
                select(QualityCheck)
                .where(
                    QualityCheck.operation_execution_id == execution_id,
                    QualityCheck.user_id == user_id,
                )
                .order_by(QualityCheck.checked_at.desc(), QualityCheck.created_at.desc())
            ).all()
        )

        return [
            QualityCheckResponse(
                id=q.id,
                user_id=q.user_id,
                production_order_id=q.production_order_id,
                operation_execution_id=q.operation_execution_id,
                production_step_id=q.production_step_id,
                result=q.result,
                defect_severity=q.defect_severity,
                defect_type=q.defect_type,
                notes=q.notes,
                checked_by=q.checked_by,
                checked_at=q.checked_at,
                created_at=q.created_at,
                updated_at=q.updated_at,
                step_number=step.step_number if step else None,
                stage_name=step.stage_name if step else None,
                quality_checkpoint=step.quality_checkpoint if step else None,
            )
            for q in records
        ]

    @staticmethod
    def get_order_quality_summary(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
    ) -> OrderQualitySummaryResponse:
        """
        Returns authoritative quality check summary metrics for an entire production order.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        order = db.scalar(
            select(ProductionOrder)
            .where(
                ProductionOrder.id == order_id,
                ProductionOrder.user_id == user_id,
            )
        )
        if not order:
            raise AppException(
                "Production order not found.",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        metrics = ProductionExecutionService.calculate_order_quality_metrics(
            db, user_id, order_id
        )

        return OrderQualitySummaryResponse(
            order_id=metrics["order_id"],
            total_operations=metrics["total_operations"],
            completed_operations=metrics["completed_operations"],
            passed=metrics["passed"],
            failed=metrics["failed"],
            rework=metrics["rework"],
            pending_quality_checks=metrics["pending_quality_checks"],
            quality_gate_passed=metrics["quality_gate_passed"],
            items=metrics["items"],
        )

    @staticmethod
    def create_rework_execution(
        db: Session,
        user_id: Union[str, uuid.UUID],
        execution_id: Union[str, uuid.UUID],
        payload: Optional[ReworkExecutionCreate] = None,
    ) -> OperationExecution:
        """
        Explicitly initializes a controlled rework OperationExecution following a REWORK QC outcome.
        Leaves original execution historically intact and immutable in COMPLETED status.
        Initializes rework execution in READY status for shop-floor artisan/machine assignment (Phase J.3)
        and subsequent material consumption tracking (Phase J.4).
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(execution_id, str):
            execution_id = uuid.UUID(execution_id)

        # 1. Fetch original execution with lock
        original = db.scalar(
            select(OperationExecution)
            .where(
                OperationExecution.id == execution_id,
                OperationExecution.user_id == user_id,
            )
            .options(
                joinedload(OperationExecution.production_step),
                joinedload(OperationExecution.production_order),
                selectinload(OperationExecution.quality_checks),
            )
            .with_for_update()
        )
        if not original:
            raise AppException(
                "Operation execution not found.",
                code="EXECUTION_NOT_FOUND",
                status_code=404,
            )

        # 2. Must be COMPLETED
        if original.status != ExecutionStatus.COMPLETED.value:
            raise AppException(
                f"Rework can only be authorized for COMPLETED operations (current status: '{original.status}').",
                code="INVALID_EXECUTION_STATE",
                status_code=409,
            )

        # 3. Verify latest QC check is REWORK
        latest_qc = original.quality_checks[0] if (hasattr(original, "quality_checks") and original.quality_checks) else None
        if not latest_qc:
            latest_qc = db.scalar(
                select(QualityCheck)
                .where(QualityCheck.operation_execution_id == original.id)
                .order_by(QualityCheck.checked_at.desc(), QualityCheck.created_at.desc())
            )

        if not latest_qc or latest_qc.result.upper() != "REWORK":
            raise AppException(
                "Rework execution requires an explicit REWORK quality check outcome.",
                code="REWORK_NOT_PERMITTED",
                status_code=409,
            )

        # 4. Check if an active/uncompleted rework already exists for this step in this order
        active_rework = db.scalar(
            select(OperationExecution)
            .where(
                OperationExecution.production_order_id == original.production_order_id,
                OperationExecution.production_step_id == original.production_step_id,
                OperationExecution.status != ExecutionStatus.COMPLETED.value,
            )
        )
        if active_rework:
            raise AppException(
                f"An active rework execution #{active_rework.attempt_number} (status '{active_rework.status}') already exists for this step.",
                code="ACTIVE_REWORK_EXISTS",
                status_code=409,
            )

        # 5. Determine next attempt number
        max_attempt = db.scalar(
            select(func.max(OperationExecution.attempt_number))
            .where(
                OperationExecution.production_order_id == original.production_order_id,
                OperationExecution.production_step_id == original.production_step_id,
            )
        ) or 1
        next_attempt = max_attempt + 1

        # 6. Create rework execution in READY state
        custom_notes = payload.operator_notes.strip() if (payload and payload.operator_notes) else None
        rework_notes = (
            f"Rework attempt #{next_attempt} authorized following QC inspection on execution {original.id}."
        )
        if custom_notes:
            rework_notes = f"{rework_notes}\nNotes: {custom_notes}"

        rework_ex = OperationExecution(
            id=uuid.uuid4(),
            user_id=user_id,
            production_order_id=original.production_order_id,
            production_step_id=original.production_step_id,
            scheduled_task_id=original.scheduled_task_id,
            worker_id=None,
            machine_id=None,
            status=ExecutionStatus.READY.value,
            planned_start_time=None,
            planned_end_time=None,
            planned_duration_hours=original.planned_duration_hours,
            execution_type="rework",
            rework_of_execution_id=original.id,
            attempt_number=next_attempt,
            operator_notes=rework_notes,
        )
        db.add(rework_ex)

        # 7. Update order status: since an uncompleted rework exists, order cannot be completed
        order = original.production_order
        if not order:
            order = db.scalar(
                select(ProductionOrder)
                .where(ProductionOrder.id == original.production_order_id)
                .with_for_update()
            )
        if order and order.status == "completed":
            order.status = "in_progress"

        try:
            db.commit()
            db.refresh(rework_ex)
        except Exception:
            db.rollback()
            raise

        return rework_ex

    @staticmethod
    def complete_order(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
    ) -> ProductionOrder:
        """
        Explicitly completes a ProductionOrder after validating that all manufacturing operations
        have completed and the Phase J.5 Quality Control gate has passed with 100% PASS outcomes.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        order = db.scalar(
            select(ProductionOrder)
            .where(
                ProductionOrder.id == order_id,
                ProductionOrder.user_id == user_id,
            )
            .with_for_update()
        )
        if not order:
            raise AppException(
                "Production order not found.",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        metrics = ProductionExecutionService.calculate_order_quality_metrics(
            db, user_id, order_id
        )

        if not metrics["quality_gate_passed"]:
            raise AppException(
                f"Cannot complete order: quality gate has not passed (passed={metrics['passed']}/{metrics['total_operations']}, "
                f"failed={metrics['failed']}, rework={metrics['rework']}, pending_qc={metrics['pending_quality_checks']}).",
                code="QUALITY_GATE_NOT_MET",
                status_code=409,
            )

        order.status = "completed"
        try:
            db.commit()
            db.refresh(order)
        except Exception:
            db.rollback()
            raise

        return order


production_execution_service = ProductionExecutionService()

