"""
Production Optimization & Scheduling Service using Google OR-Tools CP-SAT Solver.
Solves multi-order, multi-artisan, multi-machine job-shop scheduling models with
strict conflict prevention, skill matching, operation precedence, and priority-weighted objectives.
"""

import math
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from ortools.sat.python import cp_model
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppException
from app.models.design import Design
from app.models.production import Machine, ProductionOrder, Worker
from app.models.schedule import ProductionSchedule, ScheduledTask
from app.schemas.optimization import (
    OptimizationMetrics,
    OptimizationRequest,
    OptimizationResponse,
    ProductionScheduleListResponse,
    ProductionScheduleResponse,
    ScheduledTaskResponse,
    SolverStatusEnum,
)

# Priority weight multipliers for CP-SAT objective penalty
PRIORITY_WEIGHTS: Dict[str, int] = {
    "urgent": 50,
    "high": 20,
    "medium": 5,
    "low": 1,
}

# Standard jewellery manufacturing operations
# (name, eligible_skills, required_machine_types, base_hours, per_unit_hours)
OPERATION_DEFS = [
    {
        "name": "Casting & Metallurgy",
        "skills": {"casting", "general"},
        "machines": {"casting_furnace", "general"},
        "base_hours": 2,
        "per_unit_hours": 0.5,
    },
    {
        "name": "Stone Setting & Assembly",
        "skills": {"stone_setting", "cad_design", "general"},
        "machines": set(),  # Benchwork
        "base_hours": 2,
        "per_unit_hours": 0.75,
    },
    {
        "name": "Polishing & Finishing",
        "skills": {"polishing", "engraving", "general"},
        "machines": {"polishing_lathe", "laser_engraver", "ultrasonic_cleaner", "general"},
        "base_hours": 1,
        "per_unit_hours": 0.5,
    },
]


class ProductionOptimizationService:
    """Service encapsulating OR-Tools CP-SAT scheduling formulation and persistence."""

    def optimize(
        self,
        db: Session,
        user_id: uuid.UUID,
        request: OptimizationRequest,
    ) -> OptimizationResponse:
        """
        Execute CP-SAT production scheduling optimization for a tenant's orders and workshop assets.
        """
        start_clock = time.perf_counter()

        # 1. Resolve planning horizon & start date
        start_date = request.start_date or datetime.now(timezone.utc)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)

        horizon_hours = request.horizon_days * 24

        # 2. Fetch user orders
        query = (
            select(ProductionOrder)
            .where(ProductionOrder.user_id == user_id)
            .options(selectinload(ProductionOrder.design))
        )
        if request.order_ids:
            query = query.where(ProductionOrder.id.in_(request.order_ids))
        else:
            query = query.where(ProductionOrder.status.in_(["pending", "in_progress"]))

        orders: List[ProductionOrder] = list(db.execute(query).scalars().all())

        if not orders:
            return OptimizationResponse(
                status="success",
                solver_status=SolverStatusEnum.OPTIMAL,
                message="No eligible production orders found to schedule.",
                schedule=[],
                unscheduled_order_ids=[],
                metrics=OptimizationMetrics(
                    solver_runtime_ms=(time.perf_counter() - start_clock) * 1000
                ),
                infeasibility_reasons=[],
            )

        # 3. Fetch active workers and machines
        workers: List[Worker] = list(
            db.execute(
                select(Worker)
                .where(Worker.user_id == user_id, Worker.is_available.is_(True))
            ).scalars().all()
        )

        machines: List[Machine] = list(
            db.execute(
                select(Machine)
                .where(Machine.user_id == user_id, Machine.is_available.is_(True))
            ).scalars().all()
        )

        # 4. Infeasibility pre-checks
        infeasibility_reasons: List[str] = []
        if not workers:
            infeasibility_reasons.append("No active workshop artisans/workers available.")

        # Calculate estimated total required hours vs available capacity
        total_work_hours_needed = 0.0
        for order in orders:
            for op_def in OPERATION_DEFS:
                dur = math.ceil(op_def["base_hours"] + op_def["per_unit_hours"] * max(1, order.quantity))
                total_work_hours_needed += dur

        total_worker_capacity_hours = sum(w.capacity_hours_per_day for w in workers) * request.horizon_days

        if workers and total_worker_capacity_hours < total_work_hours_needed:
            infeasibility_reasons.append(
                f"Total required production duration ({int(total_work_hours_needed)}h) exceeds total available "
                f"artisan capacity ({int(total_worker_capacity_hours)}h) within the {request.horizon_days}-day horizon."
            )

        if infeasibility_reasons:
            return OptimizationResponse(
                status="infeasible",
                solver_status=SolverStatusEnum.INFEASIBLE,
                message="Schedule could not be generated due to resource constraints.",
                schedule=[],
                unscheduled_order_ids=[o.id for o in orders],
                metrics=OptimizationMetrics(
                    total_orders_unscheduled=len(orders),
                    solver_runtime_ms=(time.perf_counter() - start_clock) * 1000,
                ),
                infeasibility_reasons=infeasibility_reasons,
            )

        # 5. Build CP-SAT Model
        model = cp_model.CpModel()

        # Data structures for intervals and assignments
        # key: (order_id, op_idx) -> {start, end, duration, interval, worker_vars, machine_vars}
        task_vars: Dict[Tuple[uuid.UUID, int], Dict[str, Any]] = {}
        worker_intervals: Dict[uuid.UUID, List[cp_model.IntervalVar]] = {w.id: [] for w in workers}
        machine_intervals: Dict[uuid.UUID, List[cp_model.IntervalVar]] = {m.id: [] for m in machines}

        order_tardiness_vars: List[Tuple[cp_model.IntVar, int]] = []
        order_end_vars: List[cp_model.IntVar] = []

        for o_idx, order in enumerate(orders):
            prev_end_var: Optional[cp_model.IntVar] = None

            for op_idx, op_def in enumerate(OPERATION_DEFS):
                dur_hours = max(1, math.ceil(op_def["base_hours"] + op_def["per_unit_hours"] * max(1, order.quantity)))

                # Start and End integer variables (bounded within horizon)
                start_var = model.NewIntVar(0, horizon_hours, f"start_o{o_idx}_op{op_idx}")
                end_var = model.NewIntVar(0, horizon_hours, f"end_o{o_idx}_op{op_idx}")
                interval_var = model.NewIntervalVar(
                    start_var,
                    dur_hours,
                    end_var,
                    f"interval_o{o_idx}_op{op_idx}",
                )

                # Precedence constraint: current operation must start after previous finishes
                if prev_end_var is not None:
                    model.Add(start_var >= prev_end_var)

                prev_end_var = end_var

                # Filter eligible workers (matching skill or general fallback)
                eligible_workers = [
                    w for w in workers
                    if w.skill.lower() in op_def["skills"] or w.skill.lower() == "general" or "general" in op_def["skills"]
                ]
                if not eligible_workers:
                    # Fallback to any active worker so solver doesn't fail if all workers have unique custom skills
                    eligible_workers = workers

                worker_b_vars: Dict[uuid.UUID, cp_model.IntVar] = {}
                for w in eligible_workers:
                    b_var = model.NewBoolVar(f"w_o{o_idx}_op{op_idx}_w{w.id}")
                    worker_b_vars[w.id] = b_var
                    opt_interval = model.NewOptionalIntervalVar(
                        start_var,
                        dur_hours,
                        end_var,
                        b_var,
                        f"opt_w_o{o_idx}_op{op_idx}_w{w.id}",
                    )
                    worker_intervals[w.id].append(opt_interval)

                # Exactly one worker assigned per operation
                model.AddExactlyOne(list(worker_b_vars.values()))

                # Filter eligible machines
                machine_b_vars: Dict[uuid.UUID, cp_model.IntVar] = {}
                if op_def["machines"] and machines:
                    eligible_machines = [
                        m for m in machines
                        if m.machine_type.lower() in op_def["machines"] or m.machine_type.lower() == "general"
                    ]
                    if eligible_machines:
                        for m in eligible_machines:
                            mb_var = model.NewBoolVar(f"m_o{o_idx}_op{op_idx}_m{m.id}")
                            machine_b_vars[m.id] = mb_var
                            opt_m_interval = model.NewOptionalIntervalVar(
                                start_var,
                                dur_hours,
                                end_var,
                                mb_var,
                                f"opt_m_o{o_idx}_op{op_idx}_m{m.id}",
                            )
                            machine_intervals[m.id].append(opt_m_interval)
                        model.AddExactlyOne(list(machine_b_vars.values()))

                task_vars[(order.id, op_idx)] = {
                    "order": order,
                    "op_def": op_def,
                    "duration": dur_hours,
                    "start_var": start_var,
                    "end_var": end_var,
                    "interval_var": interval_var,
                    "worker_vars": worker_b_vars,
                    "machine_vars": machine_b_vars,
                }

            # Final operation end time represents order completion
            final_end_var = prev_end_var
            order_end_vars.append(final_end_var)

            # Deadline penalty formulation
            deadline_utc = order.deadline
            if deadline_utc.tzinfo is None:
                deadline_utc = deadline_utc.replace(tzinfo=timezone.utc)

            deadline_hour = max(0, int((deadline_utc - start_date).total_seconds() / 3600))
            tardiness_var = model.NewIntVar(0, horizon_hours, f"tardiness_o{o_idx}")
            # tardiness >= final_end - deadline_hour
            model.Add(tardiness_var >= final_end_var - deadline_hour)

            p_weight = PRIORITY_WEIGHTS.get(order.priority.lower(), 5)
            order_tardiness_vars.append((tardiness_var, p_weight))

        # 6. Non-overlapping resource constraints
        for w_id, intervals in worker_intervals.items():
            if intervals:
                model.AddNoOverlap(intervals)

        for m_id, m_inter in machine_intervals.items():
            if m_inter:
                model.AddNoOverlap(m_inter)

        # 7. Makespan objective
        makespan_var = model.NewIntVar(0, horizon_hours, "makespan")
        for end_v in order_end_vars:
            model.Add(makespan_var >= end_v)

        # Objective: minimize weighted tardiness + 2 * makespan
        obj_terms = [tardiness_var * weight for tardiness_var, weight in order_tardiness_vars]
        obj_terms.append(makespan_var * 2)
        model.Minimize(sum(obj_terms))

        # 8. Solve CP-SAT model
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(request.time_limit_seconds)
        solver.parameters.num_search_workers = 4

        status = solver.Solve(model)
        runtime_sec = time.perf_counter() - start_clock

        # Map CP-SAT status
        status_map = {
            cp_model.OPTIMAL: SolverStatusEnum.OPTIMAL,
            cp_model.FEASIBLE: SolverStatusEnum.FEASIBLE,
            cp_model.INFEASIBLE: SolverStatusEnum.INFEASIBLE,
            cp_model.MODEL_INVALID: SolverStatusEnum.MODEL_INVALID,
            cp_model.UNKNOWN: SolverStatusEnum.UNKNOWN,
        }
        resolved_status = status_map.get(status, SolverStatusEnum.UNKNOWN)

        if resolved_status not in [SolverStatusEnum.OPTIMAL, SolverStatusEnum.FEASIBLE]:
            return OptimizationResponse(
                status="infeasible",
                solver_status=resolved_status,
                message="CP-SAT solver determined no feasible schedule exists within the given constraints.",
                schedule=[],
                unscheduled_order_ids=[o.id for o in orders],
                metrics=OptimizationMetrics(
                    total_orders_unscheduled=len(orders),
                    solver_runtime_ms=runtime_sec * 1000,
                ),
                infeasibility_reasons=[
                    "The solver could not fit all manufacturing operations within the planning horizon.",
                    "Consider extending the horizon days or adding additional artisan capacity.",
                ],
            )

        # 9. Extract and validate solution
        worker_lookup = {w.id: w for w in workers}
        machine_lookup = {m.id: m for m in machines}

        scheduled_task_items: List[ScheduledTaskResponse] = []
        worker_busy_hours: Dict[uuid.UUID, float] = {w.id: 0.0 for w in workers}
        machine_busy_hours: Dict[uuid.UUID, float] = {m.id: 0.0 for m in machines}
        orders_on_time = 0
        orders_overdue = 0

        # Sort tasks by start time
        sorted_keys = sorted(task_vars.keys(), key=lambda k: (solver.Value(task_vars[k]["start_var"]), k[1]))

        for key in sorted_keys:
            t_data = task_vars[key]
            order: ProductionOrder = t_data["order"]
            op_def = t_data["op_def"]
            dur = t_data["duration"]

            start_h = solver.Value(t_data["start_var"])
            end_h = solver.Value(t_data["end_var"])

            task_start_dt = start_date + timedelta(hours=start_h)
            task_end_dt = start_date + timedelta(hours=end_h)

            # Resolve assigned worker
            assigned_worker_id: Optional[uuid.UUID] = None
            for w_id, b_var in t_data["worker_vars"].items():
                if solver.Value(b_var) == 1:
                    assigned_worker_id = w_id
                    worker_busy_hours[w_id] += dur
                    break

            # Resolve assigned machine
            assigned_machine_id: Optional[uuid.UUID] = None
            for m_id, mb_var in t_data["machine_vars"].items():
                if solver.Value(mb_var) == 1:
                    assigned_machine_id = m_id
                    machine_busy_hours[m_id] += dur
                    break

            assigned_worker = worker_lookup.get(assigned_worker_id) if assigned_worker_id else None
            assigned_machine = machine_lookup.get(assigned_machine_id) if assigned_machine_id else None

            # Deadline check
            deadline_utc = order.deadline
            if deadline_utc.tzinfo is None:
                deadline_utc = deadline_utc.replace(tzinfo=timezone.utc)
            is_task_overdue = task_end_dt > deadline_utc

            design_name = order.design.name if order.design else "Custom Jewellery"
            design_img = (order.design.rendered_image_url or order.design.sketch_image_url) if order.design else None

            task_res = ScheduledTaskResponse(
                id=uuid.uuid4(),
                order_id=order.id,
                design_id=order.design_id,
                design_name=design_name,
                design_image_url=design_img,
                quantity=order.quantity,
                priority=order.priority,
                worker_id=assigned_worker_id,
                worker_name=assigned_worker.name if assigned_worker else "Unassigned",
                worker_skill=assigned_worker.skill if assigned_worker else None,
                machine_id=assigned_machine_id,
                machine_name=assigned_machine.name if assigned_machine else None,
                machine_type=assigned_machine.machine_type if assigned_machine else None,
                operation_name=op_def["name"],
                start_time=task_start_dt,
                end_time=task_end_dt,
                duration_hours=float(dur),
                sequence_order=key[1] + 1,
                is_overdue=is_task_overdue,
            )
            scheduled_task_items.append(task_res)

        # Count order-level timeliness
        makespan_val = float(solver.Value(makespan_var))
        for order in orders:
            order_tasks = [t for t in scheduled_task_items if t.order_id == order.id]
            if order_tasks:
                max_end = max(t.end_time for t in order_tasks)
                deadline_utc = order.deadline
                if deadline_utc.tzinfo is None:
                    deadline_utc = deadline_utc.replace(tzinfo=timezone.utc)
                if max_end > deadline_utc:
                    orders_overdue += 1
                else:
                    orders_on_time += 1

        # Calculate utilization rates
        total_avail_worker_h = sum(w.capacity_hours_per_day for w in workers) * request.horizon_days
        total_used_worker_h = sum(worker_busy_hours.values())
        worker_util_pct = (
            round((total_used_worker_h / total_avail_worker_h) * 100.0, 1)
            if total_avail_worker_h > 0
            else 0.0
        )

        total_avail_machine_h = sum(m.capacity_hours_per_day for m in machines) * request.horizon_days
        total_used_machine_h = sum(machine_busy_hours.values())
        machine_util_pct = (
            round((total_used_machine_h / total_avail_machine_h) * 100.0, 1)
            if total_avail_machine_h > 0
            else 0.0
        )

        metrics = OptimizationMetrics(
            makespan_hours=makespan_val,
            total_orders_scheduled=len(orders),
            total_orders_unscheduled=0,
            worker_utilization_pct=worker_util_pct,
            machine_utilization_pct=machine_util_pct,
            orders_on_time=orders_on_time,
            orders_overdue=orders_overdue,
            solver_runtime_ms=round(runtime_sec * 1000, 2),
        )

        # 10. Post-solve Schedule Validation
        self._validate_schedule(scheduled_task_items, workers, machines)

        # 11. Persist schedule if requested
        schedule_id: Optional[uuid.UUID] = None
        if request.persist_schedule:
            schedule_entity = ProductionSchedule(
                id=uuid.uuid4(),
                user_id=user_id,
                name=request.schedule_name or f"Optimized Schedule ({start_date.strftime('%b %d, %Y')})",
                start_date=start_date,
                horizon_days=request.horizon_days,
                solver_status=resolved_status.value,
                makespan_hours=makespan_val,
                total_orders_scheduled=len(orders),
                total_orders_unscheduled=0,
                worker_utilization_pct=worker_util_pct,
                machine_utilization_pct=machine_util_pct,
                runtime_seconds=round(runtime_sec, 3),
            )
            db.add(schedule_entity)
            db.flush()

            for item in scheduled_task_items:
                st = ScheduledTask(
                    id=item.id or uuid.uuid4(),
                    schedule_id=schedule_entity.id,
                    order_id=item.order_id,
                    worker_id=item.worker_id,
                    machine_id=item.machine_id,
                    operation_name=item.operation_name,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    duration_hours=item.duration_hours,
                    sequence_order=item.sequence_order,
                    is_overdue=item.is_overdue,
                )
                db.add(st)

            db.commit()
            schedule_id = schedule_entity.id

        return OptimizationResponse(
            status="success" if resolved_status == SolverStatusEnum.OPTIMAL else "feasible",
            solver_status=resolved_status,
            message=f"Production schedule generated successfully ({resolved_status.value}).",
            schedule=scheduled_task_items,
            unscheduled_order_ids=[],
            metrics=metrics,
            infeasibility_reasons=[],
            schedule_id=schedule_id,
        )

    def _validate_schedule(
        self,
        tasks: List[ScheduledTaskResponse],
        workers: List[Worker],
        machines: List[Machine],
    ) -> None:
        """
        Validate generated schedule to ensure zero overlapping worker/machine intervals
        and strictly positive durations.
        """
        # Check positive durations
        for t in tasks:
            if t.duration_hours <= 0:
                raise AppException(message=f"Task duration must be > 0: {t.operation_name}", code="SCHEDULE_VALIDATION_FAILED", status_code=422)
            if t.end_time <= t.start_time:
                raise AppException(message=f"Task end time must be after start time: {t.operation_name}", code="SCHEDULE_VALIDATION_FAILED", status_code=422)

        # Check worker overlaps
        worker_tasks: Dict[uuid.UUID, List[ScheduledTaskResponse]] = {}
        for t in tasks:
            if t.worker_id:
                worker_tasks.setdefault(t.worker_id, []).append(t)

        for w_id, w_tlist in worker_tasks.items():
            sorted_wt = sorted(w_tlist, key=lambda x: x.start_time)
            for i in range(len(sorted_wt) - 1):
                if sorted_wt[i].end_time > sorted_wt[i + 1].start_time:
                    raise AppException(
                        message=f"Worker conflict detected between tasks {sorted_wt[i].operation_name} and {sorted_wt[i+1].operation_name}",
                        code="SCHEDULE_VALIDATION_FAILED",
                        status_code=422,
                    )

        # Check machine overlaps
        machine_tasks: Dict[uuid.UUID, List[ScheduledTaskResponse]] = {}
        for t in tasks:
            if t.machine_id:
                machine_tasks.setdefault(t.machine_id, []).append(t)

        for m_id, m_tlist in machine_tasks.items():
            sorted_mt = sorted(m_tlist, key=lambda x: x.start_time)
            for i in range(len(sorted_mt) - 1):
                if sorted_mt[i].end_time > sorted_mt[i + 1].start_time:
                    raise AppException(
                        message=f"Machine conflict detected between tasks {sorted_mt[i].operation_name} and {sorted_mt[i+1].operation_name}",
                        code="SCHEDULE_VALIDATION_FAILED",
                        status_code=422,
                    )

    def get_user_schedules(
        self,
        db: Session,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> ProductionScheduleListResponse:
        """Retrieve paginated historical schedules for a user."""
        total = db.scalar(
            select(func.count(ProductionSchedule.id)).where(ProductionSchedule.user_id == user_id)
        ) or 0

        schedules = list(
            db.execute(
                select(ProductionSchedule)
                .where(ProductionSchedule.user_id == user_id)
                .options(
                    selectinload(ProductionSchedule.tasks)
                    .selectinload(ScheduledTask.order)
                    .selectinload(ProductionOrder.design),
                    selectinload(ProductionSchedule.tasks).selectinload(ScheduledTask.worker),
                    selectinload(ProductionSchedule.tasks).selectinload(ScheduledTask.machine),
                )
                .order_by(ProductionSchedule.created_at.desc())
                .offset(offset)
                .limit(limit)
            ).scalars().all()
        )

        items = [self._to_schedule_response(s) for s in schedules]
        return ProductionScheduleListResponse(items=items, total=total)

    def get_schedule_by_id(
        self,
        db: Session,
        user_id: uuid.UUID,
        schedule_id: uuid.UUID,
    ) -> ProductionScheduleResponse:
        """Retrieve a specific saved schedule with all task details."""
        schedule = db.execute(
            select(ProductionSchedule)
            .where(ProductionSchedule.id == schedule_id, ProductionSchedule.user_id == user_id)
            .options(
                selectinload(ProductionSchedule.tasks)
                .selectinload(ScheduledTask.order)
                .selectinload(ProductionOrder.design),
                selectinload(ProductionSchedule.tasks).selectinload(ScheduledTask.worker),
                selectinload(ProductionSchedule.tasks).selectinload(ScheduledTask.machine),
            )
        ).scalar_one_or_none()

        if not schedule:
            raise AppException(message="Production schedule not found or access denied.", code="SCHEDULE_NOT_FOUND", status_code=404)

        return self._to_schedule_response(schedule)

    def delete_schedule(
        self,
        db: Session,
        user_id: uuid.UUID,
        schedule_id: uuid.UUID,
    ) -> None:
        """Delete a saved production schedule and cascade its tasks."""
        schedule = db.execute(
            select(ProductionSchedule).where(
                ProductionSchedule.id == schedule_id,
                ProductionSchedule.user_id == user_id,
            )
        ).scalar_one_or_none()

        if not schedule:
            raise AppException(message="Production schedule not found or access denied.", code="SCHEDULE_NOT_FOUND", status_code=404)

        db.delete(schedule)
        db.commit()

    def _to_schedule_response(self, schedule: ProductionSchedule) -> ProductionScheduleResponse:
        """Format ORM schedule into Pydantic schema."""
        task_responses: List[ScheduledTaskResponse] = []
        for t in schedule.tasks:
            design_name = t.order.design.name if t.order and t.order.design else "Custom Jewellery"
            design_img = (
                (t.order.design.rendered_image_url or t.order.design.sketch_image_url)
                if t.order and t.order.design
                else None
            )
            task_responses.append(
                ScheduledTaskResponse(
                    id=t.id,
                    order_id=t.order_id,
                    design_id=t.order.design_id if t.order else None,
                    design_name=design_name,
                    design_image_url=design_img,
                    quantity=t.order.quantity if t.order else 1,
                    priority=t.order.priority if t.order else "medium",
                    worker_id=t.worker_id,
                    worker_name=t.worker.name if t.worker else "Unassigned",
                    worker_skill=t.worker.skill if t.worker else None,
                    machine_id=t.machine_id,
                    machine_name=t.machine.name if t.machine else None,
                    machine_type=t.machine.machine_type if t.machine else None,
                    operation_name=t.operation_name,
                    start_time=t.start_time,
                    end_time=t.end_time,
                    duration_hours=t.duration_hours,
                    sequence_order=t.sequence_order,
                    is_overdue=t.is_overdue,
                )
            )

        return ProductionScheduleResponse(
            id=schedule.id,
            user_id=schedule.user_id,
            name=schedule.name,
            start_date=schedule.start_date,
            horizon_days=schedule.horizon_days,
            solver_status=schedule.solver_status,
            makespan_hours=schedule.makespan_hours,
            total_orders_scheduled=schedule.total_orders_scheduled,
            total_orders_unscheduled=schedule.total_orders_unscheduled,
            worker_utilization_pct=schedule.worker_utilization_pct,
            machine_utilization_pct=schedule.machine_utilization_pct,
            runtime_seconds=schedule.runtime_seconds,
            tasks=task_responses,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )


production_optimization_service = ProductionOptimizationService()
