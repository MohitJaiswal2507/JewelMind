"""
Backend Unit Tests for Phase 13 Dashboard Aggregation API.
Tests authentication, multi-tenant isolation, metric aggregation, category distribution,
recent renders, upcoming deadlines, and CP-SAT schedule summaries.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.design import Design
from app.models.production import Machine, ProductionOrder, Worker
from app.models.schedule import ProductionSchedule
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.user_service import user_service


def create_test_user(db: Session, email: str = "artisan@jewelmind.com", name: str = "Artisan User") -> User:
    return user_service.create(
        db,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name=name,
        ),
    )


def get_auth_headers(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


def test_get_dashboard_overview_unauthenticated(client: TestClient):
    """Ensure unauthenticated access to /api/v1/dashboard/overview is rejected with 401."""
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 401


def test_get_dashboard_overview_empty_user(
    client: TestClient,
    db_session: Session,
):
    """Ensure empty new user gets zeroed KPIs and clean default response structure."""
    user = create_test_user(db_session, email="newbie@jewelmind.com", name="New Artisan")
    headers = get_auth_headers(user)

    response = client.get(
        "/api/v1/dashboard/overview",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["user"]["id"] == str(user.id)
    assert data["user"]["email"] == user.email
    assert data["kpis"]["total_designs"] == 0
    assert data["kpis"]["total_orders"] == 0
    assert data["kpis"]["total_workers"] == 0
    assert data["kpis"]["total_machines"] == 0
    assert data["kpis"]["on_time_delivery_rate"] == 100.0
    assert data["categories"] == []
    assert data["statuses"] == []
    assert data["priorities"] == []
    assert data["recent_designs"] == []
    assert data["recent_renders"] == []
    assert data["upcoming_deadlines"] == []
    assert data["latest_schedule"] is None
    assert data["system_status"]["backend"] == "online"


def test_get_dashboard_overview_populated_data(
    client: TestClient,
    db_session: Session,
):
    """Ensure populated designs, orders, workers, machines, and schedules are accurately aggregated."""
    user = create_test_user(db_session, email="producer@jewelmind.com", name="Master Jeweller")
    headers = get_auth_headers(user)
    now = datetime.now(timezone.utc)

    # 1. Create Designs
    d1 = Design(
        user_id=user.id,
        name="Royal Solitaire Ring",
        category="ring",
        status="rendered",
        sketch_image_url="https://example.com/sketch1.png",
        rendered_image_url="https://example.com/render1.png",
    )
    d2 = Design(
        user_id=user.id,
        name="Emerald Pendant",
        category="pendant",
        status="draft",
        sketch_image_url="https://example.com/sketch2.png",
    )
    d3 = Design(
        user_id=user.id,
        name="Diamond Tennis Bracelet",
        category="bracelet",
        status="ready",
    )
    db_session.add_all([d1, d2, d3])
    db_session.commit()

    # 2. Create Workers & Machines
    w1 = Worker(
        user_id=user.id,
        name="Artisan Rahul",
        skill="stone_setting",
        capacity_hours_per_day=8.0,
        is_available=True,
    )
    w2 = Worker(
        user_id=user.id,
        name="Artisan Priya",
        skill="polishing",
        capacity_hours_per_day=6.0,
        is_available=False,
    )
    m1 = Machine(
        user_id=user.id,
        name="Casting Lathe A",
        machine_type="casting_machine",
        capacity_hours_per_day=10.0,
        is_available=True,
    )
    db_session.add_all([w1, w2, m1])
    db_session.commit()

    # 3. Create Orders (one pending, one in_progress overdue, one completed)
    o1 = ProductionOrder(
        user_id=user.id,
        design_id=d1.id,
        quantity=5,
        priority="urgent",
        status="pending",
        deadline=now + timedelta(days=3),
    )
    o2 = ProductionOrder(
        user_id=user.id,
        design_id=d2.id,
        quantity=2,
        priority="high",
        status="in_progress",
        deadline=now - timedelta(days=1),  # Overdue
    )
    o3 = ProductionOrder(
        user_id=user.id,
        design_id=d3.id,
        quantity=10,
        priority="medium",
        status="completed",
        deadline=now + timedelta(days=5),
    )
    db_session.add_all([o1, o2, o3])
    db_session.commit()

    # 4. Create Schedule
    sched = ProductionSchedule(
        user_id=user.id,
        name="Weekly Batch Optimization",
        start_date=now,
        horizon_days=14,
        solver_status="OPTIMAL",
        makespan_hours=32.5,
        total_orders_scheduled=2,
        total_orders_unscheduled=0,
        worker_utilization_pct=85.0,
        machine_utilization_pct=75.0,
        runtime_seconds=0.12,
    )
    db_session.add(sched)
    db_session.commit()

    # Execute request
    response = client.get(
        "/api/v1/dashboard/overview",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    kpis = data["kpis"]
    assert kpis["total_designs"] == 3
    assert kpis["active_designs"] == 3
    assert kpis["draft_designs"] == 1
    assert kpis["rendered_designs"] == 1

    assert kpis["total_orders"] == 3
    assert kpis["pending_orders"] == 1
    assert kpis["in_progress_orders"] == 1
    assert kpis["completed_orders"] == 1
    assert kpis["overdue_orders"] == 1

    assert kpis["total_workers"] == 2
    assert kpis["available_workers"] == 1
    assert kpis["total_worker_capacity_hours"] == 8.0

    assert kpis["total_machines"] == 1
    assert kpis["available_machines"] == 1
    assert kpis["total_machine_capacity_hours"] == 10.0

    assert kpis["workshop_utilization_pct"] == 80.0  # (85 + 75) / 2
    assert kpis["on_time_delivery_rate"] == 66.7  # (3 - 1) / 3 * 100

    # Verify categories
    categories = {c["name"]: c["count"] for c in data["categories"]}
    assert categories["Ring"] == 1
    assert categories["Pendant"] == 1
    assert categories["Bracelet"] == 1

    # Verify recent renders
    assert len(data["recent_renders"]) >= 1
    assert data["recent_renders"][0]["rendered_image_url"] == "https://example.com/render1.png"

    # Verify upcoming deadlines (should not contain completed order o3)
    deadlines = data["upcoming_deadlines"]
    assert len(deadlines) == 2
    assert deadlines[0]["is_overdue"] is True  # o2 is overdue
    assert deadlines[1]["is_overdue"] is False  # o1 is in 3 days

    # Verify latest schedule
    assert data["latest_schedule"] is not None
    assert data["latest_schedule"]["name"] == "Weekly Batch Optimization"
    assert data["latest_schedule"]["solver_status"] == "OPTIMAL"
    assert data["latest_schedule"]["makespan_hours"] == 32.5


def test_get_dashboard_overview_multi_tenant_isolation(
    client: TestClient,
    db_session: Session,
):
    """Ensure user A cannot see user B's designs, orders, or schedule metrics in dashboard."""
    user_a = create_test_user(db_session, email="usera@jewelmind.com", name="User A")
    user_b = create_test_user(db_session, email="userb@jewelmind.com", name="User B")

    headers_a = get_auth_headers(user_a)
    headers_b = get_auth_headers(user_b)

    # Create design for user_b
    design_b = Design(
        user_id=user_b.id,
        name="Exclusive Royal Tiara",
        category="necklace",
        status="rendered",
    )
    db_session.add(design_b)
    db_session.commit()

    # User A calls dashboard
    response_a = client.get(
        "/api/v1/dashboard/overview",
        headers=headers_a,
    )
    assert response_a.status_code == 200
    data_a = response_a.json()

    # Ensure design_b does NOT appear in user_a's dashboard
    design_names_a = [d["name"] for d in data_a["recent_designs"]]
    assert "Exclusive Royal Tiara" not in design_names_a
    assert data_a["kpis"]["total_designs"] == 0

    # User B calls dashboard
    response_b = client.get(
        "/api/v1/dashboard/overview",
        headers=headers_b,
    )
    assert response_b.status_code == 200
    data_b = response_b.json()
    assert data_b["kpis"]["total_designs"] == 1
    design_names_b = [d["name"] for d in data_b["recent_designs"]]
    assert "Exclusive Royal Tiara" in design_names_b
