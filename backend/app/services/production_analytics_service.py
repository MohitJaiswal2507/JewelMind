"""
Production Analytics Service (Phase J.7).
Provides deterministic, read-only analytics for:
1. Planned vs Actual hours, material, and variance per production order.
2. Routing operations progress and rework rate.
3. Quality inspection checks and quality gate status.
4. Schedule milestones and schedule variance.
5. Workshop-wide atelier analytics summary.
"""

import math
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.exceptions import AppException
from app.models.execution import MaterialConsumption, OperationExecution, QualityCheck
from app.models.production import ProductionOrder
from app.models.specification import ProductionGemstone, ProductionMaterial, ProductionSpecification, ProductionStep
from app.schemas.analytics import (
    ActualOrderAnalytics,
    AtelierAnalyticsSummaryResponse,
    MaterialVarianceItem,
    OperationsOrderAnalytics,
    PlannedOrderAnalytics,
    ProductionOrderAnalyticsResponse,
    QualityOrderAnalytics,
    ReworkOrderAnalytics,
    ScheduleOrderAnalytics,
    VarianceOrderAnalytics,
)
from app.schemas.execution import ExecutionStatus


class ProductionAnalyticsService:
    """Read-only analytical engine calculating deterministic planned vs actual metrics."""

    @staticmethod
    def get_order_analytics(
        db: Session,
        user_id: Union[str, uuid.UUID],
        order_id: Union[str, uuid.UUID],
    ) -> ProductionOrderAnalyticsResponse:
        """
        Computes comprehensive Planned vs Actual analytics for a single production order.
        Strictly tenant-scoped; returns 404 if the order does not exist or belongs to another tenant.
        Does not mutate any database records.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(order_id, str):
            order_id = uuid.UUID(order_id)

        # 1. Fetch order with essential relations (specification, steps, materials, gemstones, design)
        order = db.scalar(
            select(ProductionOrder)
            .where(
                ProductionOrder.id == order_id,
                ProductionOrder.user_id == user_id,
            )
            .options(
                joinedload(ProductionOrder.design),
                joinedload(ProductionOrder.specification).selectinload(ProductionSpecification.steps),
                joinedload(ProductionOrder.specification).selectinload(ProductionSpecification.materials),
                joinedload(ProductionOrder.specification).selectinload(ProductionSpecification.gemstones),
            )
        )
        if not order:
            raise AppException(
                "Production order not found.",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        # 2. Fetch all executions for this order
        executions: List[OperationExecution] = list(
            db.scalars(
                select(OperationExecution)
                .where(
                    OperationExecution.production_order_id == order_id,
                    OperationExecution.user_id == user_id,
                )
                .options(joinedload(OperationExecution.production_step))
                .order_by(OperationExecution.created_at.asc())
            ).all()
        )

        # 3. Fetch all material consumption records for this order
        consumptions: List[MaterialConsumption] = list(
            db.scalars(
                select(MaterialConsumption)
                .where(
                    MaterialConsumption.production_order_id == order_id,
                    MaterialConsumption.user_id == user_id,
                )
                .order_by(MaterialConsumption.created_at.asc())
            ).all()
        )

        # 4. Fetch all quality checks for this order
        quality_checks: List[QualityCheck] = list(
            db.scalars(
                select(QualityCheck)
                .where(
                    QualityCheck.production_order_id == order_id,
                    QualityCheck.user_id == user_id,
                )
                .order_by(QualityCheck.checked_at.desc())
            ).all()
        )

        # -------------------------------------------------------------------
        # A. TIME ANALYTICS (Planned vs Actual Hours)
        # -------------------------------------------------------------------
        spec = order.specification
        planned_hours = 0.0

        if spec and spec.steps:
            for step in spec.steps:
                step_dur = step.base_hours + (step.per_unit_hours * max(1, order.quantity))
                planned_hours += float(step_dur)
        elif executions:
            # Fallback to sum of planned_duration_hours on normal execution attempts
            for ex in executions:
                if ex.execution_type == "normal" and ex.planned_duration_hours:
                    planned_hours += ex.planned_duration_hours

        planned_hours = round(planned_hours, 2)

        # Actual hours = sum of actual net execution durations
        actual_hours = 0.0
        for ex in executions:
            if ex.actual_duration_hours is not None:
                actual_hours += ex.actual_duration_hours
        actual_hours = round(actual_hours, 2)

        time_variance_hours = round(actual_hours - planned_hours, 2)
        time_variance_percent = (
            round(((actual_hours - planned_hours) / planned_hours) * 100, 2)
            if planned_hours > 0
            else None
        )

        # -------------------------------------------------------------------
        # B. MATERIAL ANALYTICS (Planned vs Actual per Material Identity)
        # -------------------------------------------------------------------
        # Group planned materials from spec
        # Key: (material_type, material_name, unit) -> {"planned": float, "actual": float, "wastage": float}
        material_groups: Dict[Tuple[str, str, str], Dict[str, float]] = {}

        if spec:
            if spec.materials:
                for mat in spec.materials:
                    key = ("metal", f"{mat.metal_type} {mat.metal_purity}", "g")
                    if key not in material_groups:
                        material_groups[key] = {"planned": 0.0, "actual": 0.0, "wastage": 0.0}
                    if mat.estimated_weight_grams:
                        material_groups[key]["planned"] += float(mat.estimated_weight_grams * max(1, order.quantity))

            if spec.gemstones:
                for gem in spec.gemstones:
                    cut_name = getattr(gem, "cut_shape", getattr(gem, "cut", "standard")) or "standard"
                    key = ("gemstone", f"{gem.gemstone_type} ({cut_name})", "pcs")
                    if key not in material_groups:
                        material_groups[key] = {"planned": 0.0, "actual": 0.0, "wastage": 0.0}
                    material_groups[key]["planned"] += float(gem.stone_count * max(1, order.quantity))

        # Accumulate actual consumption & wastage from J.4 MaterialConsumption records
        for c in consumptions:
            # Find or create matching key
            matched_key = None
            norm_type = c.material_type.lower()
            norm_name = c.material_name.strip()
            norm_unit = c.unit.strip().lower()

            for k in material_groups.keys():
                k_type, k_name, k_unit = k
                if k_unit.lower() == norm_unit and (
                    k_name.lower() in norm_name.lower()
                    or norm_name.lower() in k_name.lower()
                    or (k_type == "metal" and "gold" in norm_type and "gold" in k_name.lower())
                ):
                    matched_key = k
                    break

            if not matched_key:
                matched_key = (c.material_type, c.material_name, c.unit)
                if matched_key not in material_groups:
                    material_groups[matched_key] = {
                        "planned": float(c.planned_quantity) if c.planned_quantity else 0.0,
                        "actual": 0.0,
                        "wastage": 0.0,
                    }

            material_groups[matched_key]["actual"] += float(c.actual_quantity)
            material_groups[matched_key]["wastage"] += float(c.wastage_quantity)

        material_variance_items: List[MaterialVarianceItem] = []
        for (m_type, m_name, m_unit), vals in material_groups.items():
            pl = round(vals["planned"], 4)
            act = round(vals["actual"], 4)
            wst = round(vals["wastage"], 4)
            net = round(act - wst, 4)
            var_qty = round(act - pl, 4)
            var_pct = round(((act - pl) / pl) * 100, 2) if pl > 0 else None
            wst_pct = round((wst / act) * 100, 2) if act > 0 else None

            material_variance_items.append(
                MaterialVarianceItem(
                    material_type=m_type,
                    material_name=m_name,
                    unit=m_unit,
                    planned_quantity=pl,
                    actual_quantity=act,
                    wastage_quantity=wst,
                    net_consumed_quantity=net,
                    variance_quantity=var_qty,
                    material_variance=var_qty,
                    variance_percent=var_pct,
                    wastage_percent=wst_pct,
                )
            )

        # -------------------------------------------------------------------
        # C. OPERATIONS STATUS DISTRIBUTION
        # -------------------------------------------------------------------
        total_ops = len(executions)
        completed_ops = sum(1 for e in executions if e.status == ExecutionStatus.COMPLETED.value)
        in_prog_ops = sum(1 for e in executions if e.status == ExecutionStatus.IN_PROGRESS.value)
        paused_ops = sum(1 for e in executions if e.status == ExecutionStatus.PAUSED.value)
        blocked_ops = sum(1 for e in executions if e.status == ExecutionStatus.BLOCKED.value)
        ready_ops = sum(1 for e in executions if e.status == ExecutionStatus.READY.value)
        pending_ops = sum(1 for e in executions if e.status == ExecutionStatus.PENDING.value)

        completion_rate = (
            round((completed_ops / total_ops) * 100, 2) if total_ops > 0 else 0.0
        )

        operations_analytics = OperationsOrderAnalytics(
            total=total_ops,
            completed=completed_ops,
            in_progress=in_prog_ops,
            paused=paused_ops,
            blocked=blocked_ops,
            ready=ready_ops,
            pending=pending_ops,
            completion_rate_percent=completion_rate,
        )

        # -------------------------------------------------------------------
        # D. QUALITY & REWORK ANALYTICS
        # -------------------------------------------------------------------
        total_checks = len(quality_checks)
        passed_checks = sum(1 for q in quality_checks if q.result.upper() == "PASS")
        failed_checks = sum(1 for q in quality_checks if q.result.upper() == "FAIL")
        rework_checks = sum(1 for q in quality_checks if q.result.upper() == "REWORK")

        # Step-level distinct QC gate determination
        step_executions: Dict[uuid.UUID, List[OperationExecution]] = {}
        for ex in executions:
            step_executions.setdefault(ex.production_step_id, []).append(ex)

        total_steps = len(step_executions) if step_executions else (len(spec.steps) if spec and spec.steps else 0)

        # Rework executions
        rework_executions = [e for e in executions if e.execution_type == "rework" or (e.attempt_number or 1) > 1]
        rework_count = len(rework_executions)
        rework_rate_pct = (
            round((rework_count / total_steps) * 100, 2) if total_steps > 0 else 0.0
        )

        steps_passed = 0
        first_pass_passed = 0
        pending_qc_count = 0

        for step_id, ex_list in step_executions.items():
            # First pass evaluation on attempt 1
            first_attempt = next((e for e in ex_list if (getattr(e, "attempt_number", 1) or 1) == 1), ex_list[0])
            first_checks = [q for q in quality_checks if q.operation_execution_id == first_attempt.id]
            if first_checks and first_checks[0].result.upper() == "PASS":
                first_pass_passed += 1

            latest_ex = max(ex_list, key=lambda e: (getattr(e, "attempt_number", 1) or 1))
            if latest_ex.status == ExecutionStatus.COMPLETED.value:
                # Latest check on this execution
                ex_checks = [q for q in quality_checks if q.operation_execution_id == latest_ex.id]
                if ex_checks and ex_checks[0].result.upper() == "PASS":
                    steps_passed += 1
                elif not ex_checks:
                    pending_qc_count += 1

        quality_gate_passed = (
            total_steps > 0
            and steps_passed == total_steps
            and completed_ops >= total_steps
        )

        # First pass yield = (first_pass_passed / total_steps) * 100
        fpy = (
            round((first_pass_passed / total_steps) * 100, 2)
            if total_steps > 0
            else None
        )

        quality_analytics = QualityOrderAnalytics(
            total_checks=total_checks,
            passed=passed_checks,
            failed=failed_checks,
            rework=rework_checks,
            pending_quality_checks=pending_qc_count,
            quality_gate_passed=quality_gate_passed,
            first_pass_yield_percent=fpy,
        )

        rework_analytics = ReworkOrderAnalytics(
            count=rework_count,
            rate_percent=rework_rate_pct,
        )

        # -------------------------------------------------------------------
        # E. SCHEDULE MILESTONES & VARIANCE
        # -------------------------------------------------------------------
        planned_starts = [e.planned_start_time for e in executions if e.planned_start_time is not None]
        planned_ends = [e.planned_end_time for e in executions if e.planned_end_time is not None]
        actual_starts = [e.actual_start_time for e in executions if e.actual_start_time is not None]
        completed_times = [e.completed_at for e in executions if e.completed_at is not None]

        min_planned_start = min(planned_starts) if planned_starts else None
        max_planned_end = max(planned_ends) if planned_ends else None
        min_actual_start = min(actual_starts) if actual_starts else None
        max_actual_completion = max(completed_times) if completed_times and len(completed_times) == completed_ops else None

        schedule_variance_hours = None
        if max_planned_end and max_actual_completion:
            diff_sec = (max_actual_completion - max_planned_end).total_seconds()
            schedule_variance_hours = round(diff_sec / 3600.0, 2)

        now_utc = datetime.now(timezone.utc)
        deadline_tz = order.deadline if order.deadline.tzinfo else order.deadline.replace(tzinfo=timezone.utc)
        is_overdue = deadline_tz < now_utc and order.status != "completed"

        schedule_analytics = ScheduleOrderAnalytics(
            planned_start=min_planned_start,
            planned_end=max_planned_end,
            actual_start=min_actual_start,
            actual_completion=max_actual_completion,
            deadline=order.deadline,
            schedule_variance_hours=schedule_variance_hours,
            is_overdue=is_overdue,
        )

        return ProductionOrderAnalyticsResponse(
            order_id=order.id,
            design_id=order.design_id,
            design_name=order.design.name if order.design else None,
            status=order.status,
            priority=order.priority,
            planned=PlannedOrderAnalytics(
                quantity=order.quantity,
                hours=planned_hours,
                materials=material_variance_items,
            ),
            actual=ActualOrderAnalytics(
                hours=actual_hours,
                materials=material_variance_items,
            ),
            variance=VarianceOrderAnalytics(
                hours=time_variance_hours,
                hours_percent=time_variance_percent,
                materials=material_variance_items,
            ),
            operations=operations_analytics,
            quality=quality_analytics,
            rework=rework_analytics,
            schedule=schedule_analytics,
        )

    @staticmethod
    def get_atelier_analytics_summary(
        db: Session,
        user_id: Union[str, uuid.UUID],
    ) -> AtelierAnalyticsSummaryResponse:
        """
        Computes aggregate Planned vs Actual workshop metrics across all orders for the user.
        Strictly tenant-scoped; read-only.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        orders = list(
            db.scalars(
                select(ProductionOrder)
                .where(ProductionOrder.user_id == user_id)
            ).all()
        )

        total_orders = len(orders)
        if total_orders == 0:
            return AtelierAnalyticsSummaryResponse(
                total_orders_analyzed=0,
                active_orders_count=0,
                completed_orders_count=0,
                total_planned_hours=0.0,
                total_actual_hours=0.0,
                net_time_variance_hours=0.0,
                average_time_variance_percent=None,
                total_rework_executions=0,
                overall_rework_rate_percent=0.0,
                total_qc_checks=0,
                overall_qc_pass_rate_percent=None,
                orders_with_rework_count=0,
                orders_quality_gate_passed_count=0,
            )

        active_count = sum(1 for o in orders if o.status in ("pending", "in_progress"))
        completed_count = sum(1 for o in orders if o.status == "completed")

        total_pl_hours = 0.0
        total_act_hours = 0.0
        orders_with_variance_pct: List[float] = []

        total_rework_ex = 0
        total_ops_count = 0
        orders_with_rework = 0
        orders_gate_passed = 0

        # Query all executions and checks for tenant once to avoid N+1
        all_executions = list(
            db.scalars(
                select(OperationExecution)
                .where(OperationExecution.user_id == user_id)
            ).all()
        )
        all_qc = list(
            db.scalars(
                select(QualityCheck)
                .where(QualityCheck.user_id == user_id)
            ).all()
        )

        order_executions_map: Dict[uuid.UUID, List[OperationExecution]] = {}
        for ex in all_executions:
            order_executions_map.setdefault(ex.production_order_id, []).append(ex)

        for order in orders:
            exs = order_executions_map.get(order.id, [])
            total_ops_count += len(exs)

            order_pl = sum(e.planned_duration_hours or 0.0 for e in exs if e.execution_type == "normal")
            order_act = sum(e.actual_duration_hours or 0.0 for e in exs)

            total_pl_hours += order_pl
            total_act_hours += order_act

            if order_pl > 0:
                pct = ((order_act - order_pl) / order_pl) * 100
                orders_with_variance_pct.append(pct)

            reworks = [e for e in exs if e.execution_type == "rework" or (e.attempt_number or 1) > 1]
            total_rework_ex += len(reworks)
            if reworks:
                orders_with_rework += 1

            if order.status == "completed":
                orders_gate_passed += 1

        total_pl_hours = round(total_pl_hours, 2)
        total_act_hours = round(total_act_hours, 2)
        net_var_hours = round(total_act_hours - total_pl_hours, 2)
        avg_var_pct = (
            round(sum(orders_with_variance_pct) / len(orders_with_variance_pct), 2)
            if orders_with_variance_pct
            else None
        )

        rework_rate_pct = (
            round((total_rework_ex / total_ops_count) * 100, 2)
            if total_ops_count > 0
            else 0.0
        )

        total_qc = len(all_qc)
        passed_qc = sum(1 for q in all_qc if q.result.upper() == "PASS")
        qc_pass_rate = (
            round((passed_qc / total_qc) * 100, 2)
            if total_qc > 0
            else None
        )

        return AtelierAnalyticsSummaryResponse(
            total_orders_analyzed=total_orders,
            active_orders_count=active_count,
            completed_orders_count=completed_count,
            total_planned_hours=total_pl_hours,
            total_actual_hours=total_act_hours,
            net_time_variance_hours=net_var_hours,
            average_time_variance_percent=avg_var_pct,
            total_rework_executions=total_rework_ex,
            overall_rework_rate_percent=rework_rate_pct,
            total_qc_checks=total_qc,
            overall_qc_pass_rate_percent=qc_pass_rate,
            orders_with_rework_count=orders_with_rework,
            orders_quality_gate_passed_count=orders_gate_passed,
        )


production_analytics_service = ProductionAnalyticsService()
