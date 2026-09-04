"""
Dashboard API Endpoints for JewelMind Phase 13.
Provides high-performance aggregated metrics, analytics distributions,
recent AI assets, workshop capacity, and optimization schedule snapshots.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.design import Design
from app.models.production import Machine, ProductionOrder, Worker
from app.models.schedule import ProductionSchedule
from app.models.user import User
from app.schemas.dashboard import (
    DashboardDeadlineOrder,
    DashboardKpis,
    DashboardLatestSchedule,
    DashboardOverviewResponse,
    DashboardRecentAsset,
    DashboardUserSummary,
    DistributionItem,
    SystemHealthStatus,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated dashboard overview",
    description="Aggregates user-scoped designs, AI render highlights, production KPIs, workshop capacity, analytics distributions, and CP-SAT schedule summaries.",
)
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DashboardOverviewResponse:
    user_id = current_user.id
    now_utc = datetime.now(timezone.utc)

    # 1. User Summary
    user_summary = DashboardUserSummary(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )

    # 2. Designs Aggregation
    designs_stmt = (
        select(Design)
        .where(Design.user_id == user_id)
        .order_by(desc(Design.updated_at))
    )
    all_designs = db.scalars(designs_stmt).all()
    total_designs = len(all_designs)
    active_designs = sum(1 for d in all_designs if d.status != "archived")
    draft_designs = sum(1 for d in all_designs if d.status == "draft")
    rendered_designs = sum(
        1 for d in all_designs if d.rendered_image_url or d.status == "rendered"
    )

    # Category distribution
    category_counts: dict[str, int] = {}
    for d in all_designs:
        cat = d.category.capitalize() if d.category else "Uncategorized"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    category_distribution: List[DistributionItem] = [
        DistributionItem(
            name=cat,
            count=count,
            percentage=round((count / total_designs) * 100, 1) if total_designs > 0 else 0.0,
        )
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # Status distribution
    status_counts: dict[str, int] = {}
    for d in all_designs:
        st = d.status.capitalize() if d.status else "Draft"
        status_counts[st] = status_counts.get(st, 0) + 1

    status_distribution: List[DistributionItem] = [
        DistributionItem(
            name=st,
            count=count,
            percentage=round((count / total_designs) * 100, 1) if total_designs > 0 else 0.0,
        )
        for st, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # 3. Production Orders Aggregation
    orders_stmt = (
        select(ProductionOrder)
        .options(joinedload(ProductionOrder.design))
        .where(ProductionOrder.user_id == user_id)
        .order_by(ProductionOrder.deadline.asc())
    )
    all_orders = db.scalars(orders_stmt).all()
    total_orders = len(all_orders)
    pending_orders = sum(1 for o in all_orders if o.status == "pending")
    in_progress_orders = sum(1 for o in all_orders if o.status == "in_progress")
    completed_orders = sum(1 for o in all_orders if o.status == "completed")
    cancelled_orders = sum(1 for o in all_orders if o.status == "cancelled")

    overdue_orders = 0
    upcoming_deadlines_list: List[DashboardDeadlineOrder] = []

    priority_counts: dict[str, int] = {}
    for o in all_orders:
        prio = o.priority.capitalize() if o.priority else "Medium"
        priority_counts[prio] = priority_counts.get(prio, 0) + 1

        deadline_tz = (
            o.deadline if o.deadline.tzinfo else o.deadline.replace(tzinfo=timezone.utc)
        )
        is_overdue = deadline_tz < now_utc and o.status not in ("completed", "cancelled")
        if is_overdue:
            overdue_orders += 1

        if o.status not in ("completed", "cancelled") and len(upcoming_deadlines_list) < 5:
            thumbnail = None
            if o.design:
                thumbnail = o.design.rendered_image_url or o.design.sketch_image_url
            upcoming_deadlines_list.append(
                DashboardDeadlineOrder(
                    id=o.id,
                    design_id=o.design_id,
                    design_name=o.design.name if o.design else None,
                    design_category=o.design.category if o.design else None,
                    design_thumbnail_url=thumbnail,
                    quantity=o.quantity,
                    priority=o.priority,
                    status=o.status,
                    deadline=o.deadline,
                    is_overdue=is_overdue,
                )
            )

    priority_distribution: List[DistributionItem] = [
        DistributionItem(
            name=prio,
            count=count,
            percentage=round((count / total_orders) * 100, 1) if total_orders > 0 else 0.0,
        )
        for prio, count in sorted(priority_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # On-time delivery rate
    active_or_completed = pending_orders + in_progress_orders + completed_orders
    if active_or_completed > 0:
        on_time_rate = round(
            max(0.0, ((active_or_completed - overdue_orders) / active_or_completed) * 100), 1
        )
    else:
        on_time_rate = 100.0

    # 4. Workers & Machines Aggregation
    workers = db.scalars(select(Worker).where(Worker.user_id == user_id)).all()
    total_workers = len(workers)
    available_workers = sum(1 for w in workers if w.is_available)
    total_worker_capacity = sum(
        w.capacity_hours_per_day for w in workers if w.is_available
    )

    machines = db.scalars(select(Machine).where(Machine.user_id == user_id)).all()
    total_machines = len(machines)
    available_machines = sum(1 for m in machines if m.is_available)
    total_machine_capacity = sum(
        m.capacity_hours_per_day for m in machines if m.is_available
    )

    # 5. Latest CP-SAT Production Schedule
    latest_schedule_row = (
        db.scalars(
            select(ProductionSchedule)
            .where(ProductionSchedule.user_id == user_id)
            .order_by(desc(ProductionSchedule.created_at))
            .limit(1)
        )
        .first()
    )

    latest_schedule = None
    workshop_utilization = 0.0
    if latest_schedule_row:
        workshop_utilization = round(
            (latest_schedule_row.worker_utilization_pct + latest_schedule_row.machine_utilization_pct) / 2.0,
            1,
        )
        latest_schedule = DashboardLatestSchedule(
            id=latest_schedule_row.id,
            name=latest_schedule_row.name,
            solver_status=latest_schedule_row.solver_status,
            makespan_hours=latest_schedule_row.makespan_hours,
            total_orders_scheduled=latest_schedule_row.total_orders_scheduled,
            total_orders_unscheduled=latest_schedule_row.total_orders_unscheduled,
            worker_utilization_pct=latest_schedule_row.worker_utilization_pct,
            machine_utilization_pct=latest_schedule_row.machine_utilization_pct,
            horizon_days=latest_schedule_row.horizon_days,
            runtime_seconds=latest_schedule_row.runtime_seconds,
            created_at=latest_schedule_row.created_at,
        )
    elif total_workers > 0 and (pending_orders + in_progress_orders) > 0:
        # Simple baseline proxy if no optimization run yet
        workshop_utilization = min(100.0, round((in_progress_orders / max(1, available_workers)) * 25.0, 1))

    # 6. Recent Designs & AI Renders
    recent_designs = [
        DashboardRecentAsset(
            id=d.id,
            name=d.name,
            category=d.category,
            status=d.status,
            sketch_image_url=d.sketch_image_url,
            rendered_image_url=d.rendered_image_url,
            ai_prompt=d.ai_prompt,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in all_designs[:6]
    ]

    recent_renders = [
        DashboardRecentAsset(
            id=d.id,
            name=d.name,
            category=d.category,
            status=d.status,
            sketch_image_url=d.sketch_image_url,
            rendered_image_url=d.rendered_image_url,
            ai_prompt=d.ai_prompt,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in all_designs
        if d.rendered_image_url or (d.sketch_image_url and d.status in ("rendering", "rendered", "ready"))
    ][:6]

    # 7. Overall KPIs
    kpis = DashboardKpis(
        total_designs=total_designs,
        active_designs=active_designs,
        draft_designs=draft_designs,
        rendered_designs=rendered_designs,
        total_orders=total_orders,
        pending_orders=pending_orders,
        in_progress_orders=in_progress_orders,
        completed_orders=completed_orders,
        overdue_orders=overdue_orders,
        total_workers=total_workers,
        available_workers=available_workers,
        total_worker_capacity_hours=round(total_worker_capacity, 1),
        total_machines=total_machines,
        available_machines=available_machines,
        total_machine_capacity_hours=round(total_machine_capacity, 1),
        workshop_utilization_pct=workshop_utilization,
        on_time_delivery_rate=on_time_rate,
    )

    return DashboardOverviewResponse(
        user=user_summary,
        kpis=kpis,
        categories=category_distribution,
        statuses=status_distribution,
        priorities=priority_distribution,
        recent_designs=recent_designs,
        recent_renders=recent_renders,
        upcoming_deadlines=upcoming_deadlines_list,
        latest_schedule=latest_schedule,
        system_status=SystemHealthStatus(
            backend="online",
            database="connected",
            ai_services="ready",
            active_gpu="RTX 4060 / Local PyTorch",
        ),
    )
