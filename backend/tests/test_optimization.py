"""
Production Optimization & CP-SAT Solver Unit & Integration Tests
Tests for Google OR-Tools CP-SAT scheduling solver, precedence constraints,
resource non-overlap, priority weighting, infeasibility diagnostics, and multi-tenant API isolation.
"""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.design import Design
from app.models.production import Machine, ProductionOrder, Worker
from app.models.schedule import ProductionSchedule, ScheduledTask
from app.models.user import User
from app.schemas.auth import UserCreate
from app.schemas.optimization import OptimizationRequest
from app.services.production_optimization_service import production_optimization_service
from app.services.user_service import user_service


# ---------------------------------------------------------------------------
# Test Fixture Helpers
# ---------------------------------------------------------------------------

def create_test_user(db: Session, email: str = "artisan.optimizer@jewelmind.com") -> User:
    """Helper to create a user for tests."""
    return user_service.create(
        db,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Optimizer Artisan Tester",
        ),
    )


def create_test_design(db: Session, user_id: uuid.UUID, name: str = "Emerald Cut Solitaire") -> Design:
    """Helper to create a design in database."""
    design = Design(
        user_id=user_id,
        name=name,
        category="Ring",
        status="ready",
        description="Diamond & gold ring for testing CP-SAT scheduler",
    )
    db.add(design)
    db.commit()
    db.refresh(design)
    return design


def get_auth_headers(user: User) -> dict:
    """Helper to generate JWT Bearer headers for a user."""
    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


def setup_workshop_environment(db: Session, user_id: uuid.UUID):
    """Creates a standard jewellery workshop with workers and machines."""
    w1 = Worker(
        user_id=user_id,
        name="Rajesh Goldsmith",
        skill="casting",
        capacity_hours_per_day=8.0,
        is_available=True,
    )
    w2 = Worker(
        user_id=user_id,
        name="Vikram Setter",
        skill="stone_setting",
        capacity_hours_per_day=8.0,
        is_available=True,
    )
    w3 = Worker(
        user_id=user_id,
        name="Priya Polisher",
        skill="polishing",
        capacity_hours_per_day=8.0,
        is_available=True,
    )
    w4 = Worker(
        user_id=user_id,
        name="Sunil Finisher",
        skill="finishing",
        capacity_hours_per_day=8.0,
        is_available=True,
    )

    m1 = Machine(
        user_id=user_id,
        name="Induction Vacuum Casting Machine",
        machine_type="casting_machine",
        capacity_hours_per_day=10.0,
        is_available=True,
    )
    m2 = Machine(
        user_id=user_id,
        name="Magnetic Rotary Tumbler & Polisher",
        machine_type="polishing_lathe",
        capacity_hours_per_day=10.0,
        is_available=True,
    )
    m3 = Machine(
        user_id=user_id,
        name="Fiber Laser Engraver & Welder",
        machine_type="laser_engraver",
        capacity_hours_per_day=10.0,
        is_available=True,
    )

    db.add_all([w1, w2, w3, w4, m1, m2, m3])
    db.commit()
    for item in [w1, w2, w3, w4, m1, m2, m3]:
        db.refresh(item)
    return {
        "workers": [w1, w2, w3, w4],
        "machines": [m1, m2, m3],
    }


# ---------------------------------------------------------------------------
# Unit Tests for ProductionOptimizationService & CP-SAT Engine
# ---------------------------------------------------------------------------

def test_optimization_service_direct_solve_feasible(db_session: Session):
    """Direct service test: Verify CP-SAT finds an optimal/feasible schedule with valid precedence."""
    user = create_test_user(db_session, "direct.solve@jewelmind.com")
    design = create_test_design(db_session, user.id, "Royal Sapphire Ring")
    setup_workshop_environment(db_session, user.id)

    # Create 2 production orders
    now = datetime.now(timezone.utc)
    o1 = ProductionOrder(
        user_id=user.id,
        design_id=design.id,
        quantity=3,
        priority="high",
        status="pending",
        deadline=now + timedelta(days=7),
    )
    o2 = ProductionOrder(
        user_id=user.id,
        design_id=design.id,
        quantity=2,
        priority="urgent",
        status="pending",
        deadline=now + timedelta(days=5),
    )
    db_session.add_all([o1, o2])
    db_session.commit()

    req = OptimizationRequest(
        horizon_days=14,
        time_limit_seconds=10,
        persist_schedule=True,
        schedule_name="Test Direct Solve Schedule",
    )

    res = production_optimization_service.optimize(db_session, user.id, req)

    assert res.status in ["success", "feasible"]
    assert res.solver_status in ["OPTIMAL", "FEASIBLE"]
    assert len(res.schedule) > 0
    assert res.metrics.makespan_hours > 0
    assert res.metrics.total_orders_scheduled == 2
    assert res.schedule_id is not None

    # Verify precedence: for each order, tasks must strictly increase in start_time according to sequence_order
    for order_id in [o1.id, o2.id]:
        order_tasks = [t for t in res.schedule if t.order_id == order_id]
        order_tasks.sort(key=lambda t: t.sequence_order)
        for i in range(len(order_tasks) - 1):
            assert order_tasks[i].end_time <= order_tasks[i + 1].start_time


def test_optimization_service_non_overlapping_resources(db_session: Session):
    """Direct service test: Verify worker and machine intervals never overlap."""
    user = create_test_user(db_session, "no.overlap@jewelmind.com")
    design = create_test_design(db_session, user.id, "Diamond Pavé Bangle")
    setup_workshop_environment(db_session, user.id)

    now = datetime.now(timezone.utc)
    orders = [
        ProductionOrder(
            user_id=user.id,
            design_id=design.id,
            quantity=2,
            priority="medium",
            status="pending",
            deadline=now + timedelta(days=7),
        )
        for _ in range(3)
    ]
    db_session.add_all(orders)
    db_session.commit()

    req = OptimizationRequest(horizon_days=14, time_limit_seconds=10, persist_schedule=False)
    res = production_optimization_service.optimize(db_session, user.id, req)

    assert res.status in ["success", "feasible"]

    # Verify worker non-overlap
    worker_tasks: dict = {}
    for task in res.schedule:
        if task.worker_id:
            worker_tasks.setdefault(task.worker_id, []).append(task)

    for wid, tasks in worker_tasks.items():
        tasks.sort(key=lambda t: t.start_time)
        for i in range(len(tasks) - 1):
            assert tasks[i].end_time <= tasks[i + 1].start_time, (
                f"Worker {wid} double-booked between {tasks[i].end_time} and {tasks[i+1].start_time}"
            )

    # Verify machine non-overlap
    machine_tasks: dict = {}
    for task in res.schedule:
        if task.machine_id:
            machine_tasks.setdefault(task.machine_id, []).append(task)

    for mid, tasks in machine_tasks.items():
        tasks.sort(key=lambda t: t.start_time)
        for i in range(len(tasks) - 1):
            assert tasks[i].end_time <= tasks[i + 1].start_time, (
                f"Machine {mid} double-booked between {tasks[i].end_time} and {tasks[i+1].start_time}"
            )


def test_optimization_service_infeasibility_diagnosis(db_session: Session):
    """Direct service test: Verify diagnostic feedback when resources are unavailable."""
    user = create_test_user(db_session, "infeasible@jewelmind.com")
    design = create_test_design(db_session, user.id, "Ornate Filigree Tiara")

    # Only add an unavailable worker
    w = Worker(
        user_id=user.id,
        name="Absent Goldsmith",
        skill="casting",
        capacity_hours_per_day=8.0,
        is_available=False,  # Unavailable!
    )
    db_session.add(w)

    now = datetime.now(timezone.utc)
    order = ProductionOrder(
        user_id=user.id,
        design_id=design.id,
        quantity=5,
        priority="urgent",
        status="pending",
        deadline=now + timedelta(days=3),
    )
    db_session.add(order)
    db_session.commit()

    req = OptimizationRequest(horizon_days=3, time_limit_seconds=5, persist_schedule=False)
    res = production_optimization_service.optimize(db_session, user.id, req)

    assert res.status == "infeasible"
    assert res.solver_status == "INFEASIBLE"
    assert len(res.infeasibility_reasons) > 0
    # Confirm feedback mentions missing/unavailable skills or equipment
    assert any("artisan" in r.lower() or "worker" in r.lower() or "skill" in r.lower() for r in res.infeasibility_reasons)


def test_optimization_service_empty_orders(db_session: Session):
    """Direct service test: Verify handling when user has no pending production orders."""
    user = create_test_user(db_session, "empty.orders@jewelmind.com")
    setup_workshop_environment(db_session, user.id)

    req = OptimizationRequest(horizon_days=14, time_limit_seconds=5)
    res = production_optimization_service.optimize(db_session, user.id, req)

    assert res.status == "success"
    assert res.solver_status == "OPTIMAL"
    assert len(res.schedule) == 0
    assert res.metrics.total_orders_scheduled == 0


# ---------------------------------------------------------------------------
# API Integration Tests (/api/v1/production/optimize & /schedules)
# ---------------------------------------------------------------------------

def test_api_optimize_production_success(client: TestClient, db_session: Session):
    """POST /api/v1/production/optimize with valid orders produces persisted schedule."""
    user = create_test_user(db_session, "api.optimize@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user.id, "Platinum Wedding Band")
    setup_workshop_environment(db_session, user.id)

    now = datetime.now(timezone.utc)
    order = ProductionOrder(
        user_id=user.id,
        design_id=design.id,
        quantity=1,
        priority="urgent",
        status="pending",
        deadline=now + timedelta(days=5),
    )
    db_session.add(order)
    db_session.commit()

    payload = {
        "horizon_days": 7,
        "time_limit_seconds": 10,
        "persist_schedule": True,
        "schedule_name": "API Test Schedule",
    }
    response = client.post("/api/v1/production/optimize", json=payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["success", "feasible"]
    assert data["solver_status"] in ["OPTIMAL", "FEASIBLE"]
    assert "metrics" in data
    assert data["metrics"]["makespan_hours"] > 0
    assert len(data["schedule"]) > 0
    assert data["schedule_id"] is not None


def test_api_get_and_list_schedules(client: TestClient, db_session: Session):
    """GET /api/v1/production/schedules lists saved schedules, and GET /{id} returns details with tasks."""
    user = create_test_user(db_session, "api.schedules@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user.id, "Solitaire Ring")
    setup_workshop_environment(db_session, user.id)

    now = datetime.now(timezone.utc)
    order = ProductionOrder(
        user_id=user.id,
        design_id=design.id,
        quantity=2,
        priority="high",
        status="pending",
        deadline=now + timedelta(days=7),
    )
    db_session.add(order)
    db_session.commit()

    # Generate a schedule
    opt_res = client.post(
        "/api/v1/production/optimize",
        json={"horizon_days": 14, "persist_schedule": True, "schedule_name": "Listed Schedule"},
        headers=headers,
    )
    assert opt_res.status_code == 200
    sched_id = opt_res.json()["schedule_id"]

    # List schedules
    list_res = client.get("/api/v1/production/schedules", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(s["id"] == sched_id for s in list_data["items"])

    # Get single schedule
    get_res = client.get(f"/api/v1/production/schedules/{sched_id}", headers=headers)
    assert get_res.status_code == 200
    sched_detail = get_res.json()
    assert sched_detail["id"] == sched_id
    assert sched_detail["name"] == "Listed Schedule"
    assert len(sched_detail["tasks"]) > 0


def test_api_delete_schedule(client: TestClient, db_session: Session):
    """DELETE /api/v1/production/schedules/{id} removes the schedule and all its tasks."""
    user = create_test_user(db_session, "api.delete.sched@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user.id, "Vintage Brooch")
    setup_workshop_environment(db_session, user.id)

    now = datetime.now(timezone.utc)
    order = ProductionOrder(
        user_id=user.id,
        design_id=design.id,
        quantity=1,
        priority="medium",
        status="pending",
        deadline=now + timedelta(days=7),
    )
    db_session.add(order)
    db_session.commit()

    opt_res = client.post(
        "/api/v1/production/optimize",
        json={"horizon_days": 14, "persist_schedule": True},
        headers=headers,
    )
    sched_id = opt_res.json()["schedule_id"]

    del_res = client.delete(f"/api/v1/production/schedules/{sched_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify it is gone
    get_res = client.get(f"/api/v1/production/schedules/{sched_id}", headers=headers)
    assert get_res.status_code == 404


def test_api_multi_tenant_isolation(client: TestClient, db_session: Session):
    """User B cannot access or optimize User A's schedules or orders."""
    user_a = create_test_user(db_session, "user.a.opt@jewelmind.com")
    user_b = create_test_user(db_session, "user.b.opt@jewelmind.com")
    headers_a = get_auth_headers(user_a)
    headers_b = get_auth_headers(user_b)

    design_a = create_test_design(db_session, user_a.id, "User A Necklace")
    setup_workshop_environment(db_session, user_a.id)

    now = datetime.now(timezone.utc)
    order_a = ProductionOrder(
        user_id=user_a.id,
        design_id=design_a.id,
        quantity=2,
        priority="high",
        status="pending",
        deadline=now + timedelta(days=7),
    )
    db_session.add(order_a)
    db_session.commit()

    # User A creates schedule
    opt_res = client.post(
        "/api/v1/production/optimize",
        json={"horizon_days": 14, "persist_schedule": True},
        headers=headers_a,
    )
    assert opt_res.status_code == 200
    sched_a_id = opt_res.json()["schedule_id"]

    # User B tries to view User A's schedule -> 404 Not Found
    get_res = client.get(f"/api/v1/production/schedules/{sched_a_id}", headers=headers_b)
    assert get_res.status_code == 404

    # User B tries to delete User A's schedule -> 404 Not Found
    del_res = client.delete(f"/api/v1/production/schedules/{sched_a_id}", headers=headers_b)
    assert del_res.status_code == 404


def test_api_unauthenticated_forbidden(client: TestClient):
    """Unauthenticated requests to optimization endpoints return 401 Unauthorized."""
    res_opt = client.post("/api/v1/production/optimize", json={})
    assert res_opt.status_code == 401

    res_list = client.get("/api/v1/production/schedules")
    assert res_list.status_code == 401
