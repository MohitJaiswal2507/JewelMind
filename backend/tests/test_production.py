"""
Production Management API & Service Tests
Tests for Production Orders, Workers, Machines, Capacity, and Aggregated Summary KPIs.
"""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.design import Design
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.user_service import user_service


def create_test_user(db: Session, email: str = "artisan@jewelmind.com") -> User:
    """Helper to create a user for tests."""
    return user_service.create(
        db,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Artisan Tester",
        ),
    )


def create_test_design(db: Session, user_id: uuid.UUID, name: str = "Diamond Solitaire Ring") -> Design:
    """Helper to create a design in database."""
    design = Design(
        user_id=user_id,
        name=name,
        category="Ring",
        status="ready",
        description="Test ring design",
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


# ---------------------------------------------------------------------------
# Production Orders Tests
# ---------------------------------------------------------------------------

def test_create_production_order_success(client: TestClient, db_session: Session):
    """Authenticated user creates a production order linked to an existing design."""
    user = create_test_user(db_session, "order_maker@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user.id, "Royal Emerald Pendant")

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {
        "design_id": str(design.id),
        "quantity": 12,
        "priority": "high",
        "status": "pending",
        "deadline": deadline,
        "notes": "Use 18K yellow gold prong setting",
    }

    response = client.post("/api/v1/production/orders", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["design_id"] == str(design.id)
    assert data["quantity"] == 12
    assert data["priority"] == "high"
    assert data["status"] == "pending"
    assert data["notes"] == "Use 18K yellow gold prong setting"
    assert data["design_name"] == "Royal Emerald Pendant"
    assert data["is_overdue"] is False
    assert data["user_id"] == str(user.id)
    assert "id" in data


def test_create_production_order_invalid_quantity(client: TestClient, db_session: Session):
    """Zero or negative quantities must be rejected."""
    user = create_test_user(db_session, "invalid_qty@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user.id)

    deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    payload = {
        "design_id": str(design.id),
        "quantity": 0,
        "priority": "medium",
        "status": "pending",
        "deadline": deadline,
    }

    response = client.post("/api/v1/production/orders", json=payload, headers=headers)
    assert response.status_code == 422


def test_create_production_order_nonexistent_design(client: TestClient, db_session: Session):
    """Production order creation with nonexistent design ID is rejected with 404."""
    user = create_test_user(db_session, "no_design@jewelmind.com")
    headers = get_auth_headers(user)

    fake_design_id = str(uuid.uuid4())
    deadline = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    payload = {
        "design_id": fake_design_id,
        "quantity": 5,
        "priority": "low",
        "status": "pending",
        "deadline": deadline,
    }

    response = client.post("/api/v1/production/orders", json=payload, headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DESIGN_NOT_FOUND"


def test_list_production_orders_and_filtering(client: TestClient, db_session: Session):
    """List production orders with status, priority, and search filters."""
    user = create_test_user(db_session, "filter_user@jewelmind.com")
    headers = get_auth_headers(user)
    d1 = create_test_design(db_session, user.id, "Sapphire Tiara")
    d2 = create_test_design(db_session, user.id, "Ruby Bracelet")

    future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    # Create 2 orders
    client.post(
        "/api/v1/production/orders",
        json={"design_id": str(d1.id), "quantity": 2, "priority": "urgent", "status": "in_progress", "deadline": future},
        headers=headers,
    )
    client.post(
        "/api/v1/production/orders",
        json={"design_id": str(d2.id), "quantity": 10, "priority": "low", "status": "pending", "deadline": future},
        headers=headers,
    )

    # All orders
    res_all = client.get("/api/v1/production/orders", headers=headers)
    assert res_all.status_code == 200
    assert res_all.json()["total"] == 2

    # Filter by status
    res_in_prog = client.get("/api/v1/production/orders?status=in_progress", headers=headers)
    assert res_in_prog.status_code == 200
    assert res_in_prog.json()["total"] == 1
    assert res_in_prog.json()["items"][0]["design_name"] == "Sapphire Tiara"

    # Filter by priority
    res_urgent = client.get("/api/v1/production/orders?priority=urgent", headers=headers)
    assert res_urgent.status_code == 200
    assert res_urgent.json()["total"] == 1

    # Search by design name
    res_search = client.get("/api/v1/production/orders?search=Ruby", headers=headers)
    assert res_search.status_code == 200
    assert res_search.json()["total"] == 1
    assert res_search.json()["items"][0]["design_name"] == "Ruby Bracelet"


def test_get_and_update_production_order(client: TestClient, db_session: Session):
    """Retrieve by ID and update production order parameters."""
    user = create_test_user(db_session, "updater@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user.id, "Gold Band")

    deadline = (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()
    create_res = client.post(
        "/api/v1/production/orders",
        json={"design_id": str(design.id), "quantity": 5, "priority": "medium", "status": "pending", "deadline": deadline},
        headers=headers,
    )
    order_id = create_res.json()["id"]

    # Get by ID
    get_res = client.get(f"/api/v1/production/orders/{order_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == order_id

    # Update order
    new_deadline = (datetime.now(timezone.utc) + timedelta(days=8)).isoformat()
    update_res = client.put(
        f"/api/v1/production/orders/{order_id}",
        json={"quantity": 20, "priority": "urgent", "status": "in_progress", "deadline": new_deadline, "notes": "Rush order"},
        headers=headers,
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["quantity"] == 20
    assert updated_data["priority"] == "urgent"
    assert updated_data["status"] == "in_progress"
    assert updated_data["notes"] == "Rush order"


def test_delete_production_order(client: TestClient, db_session: Session):
    """Delete production order returns 204 and order no longer exists."""
    user = create_test_user(db_session, "deleter@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user.id)

    deadline = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create_res = client.post(
        "/api/v1/production/orders",
        json={"design_id": str(design.id), "quantity": 1, "priority": "low", "status": "pending", "deadline": deadline},
        headers=headers,
    )
    order_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/production/orders/{order_id}", headers=headers)
    assert del_res.status_code == 204

    get_res = client.get(f"/api/v1/production/orders/{order_id}", headers=headers)
    assert get_res.status_code == 404


def test_production_order_overdue_calculation(client: TestClient, db_session: Session):
    """Orders with past deadlines and active status must be flagged as is_overdue=True."""
    user = create_test_user(db_session, "overdue_checker@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user.id, "Vintage Brooch")

    past_deadline = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    create_res = client.post(
        "/api/v1/production/orders",
        json={"design_id": str(design.id), "quantity": 3, "priority": "urgent", "status": "in_progress", "deadline": past_deadline},
        headers=headers,
    )
    assert create_res.status_code == 201
    assert create_res.json()["is_overdue"] is True

    order_id = create_res.json()["id"]
    # If status becomes completed, is_overdue becomes False
    update_res = client.put(
        f"/api/v1/production/orders/{order_id}",
        json={"status": "completed"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["is_overdue"] is False


def test_production_user_isolation(client: TestClient, db_session: Session):
    """Users cannot view, edit, or delete another user's production orders or design."""
    user_a = create_test_user(db_session, "user_a@jewelmind.com")
    user_b = create_test_user(db_session, "user_b@jewelmind.com")
    headers_a = get_auth_headers(user_a)
    headers_b = get_auth_headers(user_b)

    design_a = create_test_design(db_session, user_a.id, "User A Secret Ring")

    # User B cannot order User A's design
    deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    b_order_res = client.post(
        "/api/v1/production/orders",
        json={"design_id": str(design_a.id), "quantity": 1, "deadline": deadline},
        headers=headers_b,
    )
    assert b_order_res.status_code == 404

    # User A creates order
    a_order_res = client.post(
        "/api/v1/production/orders",
        json={"design_id": str(design_a.id), "quantity": 5, "deadline": deadline},
        headers=headers_a,
    )
    order_id = a_order_res.json()["id"]

    # User B cannot access User A's order
    assert client.get(f"/api/v1/production/orders/{order_id}", headers=headers_b).status_code == 404
    assert client.put(f"/api/v1/production/orders/{order_id}", json={"quantity": 99}, headers=headers_b).status_code == 404
    assert client.delete(f"/api/v1/production/orders/{order_id}", headers=headers_b).status_code == 404


def test_design_deletion_cascades_only_to_associated_orders(client: TestClient, db_session: Session):
    """Deleting a Design cascades to its production orders, but preserves workers, machines, and other orders."""
    user = create_test_user(db_session, "cascade_test@jewelmind.com")
    headers = get_auth_headers(user)

    d1 = create_test_design(db_session, user.id, "Ring to Delete")
    d2 = create_test_design(db_session, user.id, "Ring to Keep")

    # Add worker and machine
    w_res = client.post("/api/v1/production/workers", json={"name": "Worker C", "skill": "casting", "capacity_hours_per_day": 8.0}, headers=headers)
    m_res = client.post("/api/v1/production/machines", json={"name": "Machine C", "machine_type": "laser_engraver", "capacity_hours_per_day": 8.0}, headers=headers)
    worker_id = w_res.json()["id"]
    machine_id = m_res.json()["id"]

    # Add order for d1 and order for d2
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    o1_res = client.post("/api/v1/production/orders", json={"design_id": str(d1.id), "quantity": 10, "deadline": future}, headers=headers)
    o2_res = client.post("/api/v1/production/orders", json={"design_id": str(d2.id), "quantity": 20, "deadline": future}, headers=headers)
    o1_id = o1_res.json()["id"]
    o2_id = o2_res.json()["id"]

    # Delete design d1
    del_design_res = client.delete(f"/api/v1/designs/{d1.id}", headers=headers)
    assert del_design_res.status_code == 200

    # Verify order 1 was deleted by cascade
    assert client.get(f"/api/v1/production/orders/{o1_id}", headers=headers).status_code == 404

    # Verify order 2 still exists
    assert client.get(f"/api/v1/production/orders/{o2_id}", headers=headers).status_code == 200

    # Verify worker and machine are unaffected
    assert client.get(f"/api/v1/production/workers/{worker_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/production/machines/{machine_id}", headers=headers).status_code == 200



# ---------------------------------------------------------------------------
# Workers Tests
# ---------------------------------------------------------------------------

def test_worker_crud_and_capacity_validation(client: TestClient, db_session: Session):
    """Worker CRUD, validation, availability toggling, and capacity constraint checks."""
    user = create_test_user(db_session, "artisan_boss@jewelmind.com")
    headers = get_auth_headers(user)

    # 1. Invalid capacity (< 0) rejected
    bad_payload = {"name": "Master Goldsmith", "skill": "stone_setting", "capacity_hours_per_day": -2.0}
    bad_res = client.post("/api/v1/production/workers", json=bad_payload, headers=headers)
    assert bad_res.status_code == 422

    # 2. Blank name rejected
    blank_name = {"name": "   ", "skill": "polishing", "capacity_hours_per_day": 8.0}
    assert client.post("/api/v1/production/workers", json=blank_name, headers=headers).status_code == 422

    # 3. Create valid worker
    create_payload = {
        "name": "Rajesh Sharma",
        "skill": "stone_setting",
        "capacity_hours_per_day": 7.5,
        "is_available": True,
    }
    create_res = client.post("/api/v1/production/workers", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    w_data = create_res.json()
    assert w_data["name"] == "Rajesh Sharma"
    assert w_data["skill"] == "stone_setting"
    assert w_data["capacity_hours_per_day"] == 7.5
    assert w_data["is_available"] is True
    worker_id = w_data["id"]

    # 4. List workers
    list_res = client.get("/api/v1/production/workers", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # 5. Update worker
    update_res = client.put(
        f"/api/v1/production/workers/{worker_id}",
        json={"capacity_hours_per_day": 8.0, "is_available": False},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["capacity_hours_per_day"] == 8.0
    assert update_res.json()["is_available"] is False

    # 6. Delete worker
    del_res = client.delete(f"/api/v1/production/workers/{worker_id}", headers=headers)
    assert del_res.status_code == 204
    assert client.get(f"/api/v1/production/workers/{worker_id}", headers=headers).status_code == 404


# ---------------------------------------------------------------------------
# Machines Tests
# ---------------------------------------------------------------------------

def test_machine_crud_and_capacity_validation(client: TestClient, db_session: Session):
    """Machine CRUD, validation, availability toggles, and equipment types."""
    user = create_test_user(db_session, "machine_admin@jewelmind.com")
    headers = get_auth_headers(user)

    # 1. Invalid capacity rejected
    bad_res = client.post(
        "/api/v1/production/machines",
        json={"name": "Laser Unit", "machine_type": "laser_engraver", "capacity_hours_per_day": -5.0},
        headers=headers,
    )
    assert bad_res.status_code == 422

    # 2. Create valid machine
    create_payload = {
        "name": "Fiber Laser Marker X2",
        "machine_type": "laser_engraver",
        "capacity_hours_per_day": 10.0,
        "is_available": True,
    }
    create_res = client.post("/api/v1/production/machines", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    m_data = create_res.json()
    assert m_data["name"] == "Fiber Laser Marker X2"
    assert m_data["machine_type"] == "laser_engraver"
    assert m_data["capacity_hours_per_day"] == 10.0
    machine_id = m_data["id"]

    # 3. List machines
    list_res = client.get("/api/v1/production/machines", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # 4. Update machine
    update_res = client.put(
        f"/api/v1/production/machines/{machine_id}",
        json={"capacity_hours_per_day": 12.0, "is_available": False},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["capacity_hours_per_day"] == 12.0
    assert update_res.json()["is_available"] is False

    # 5. Delete machine
    del_res = client.delete(f"/api/v1/production/machines/{machine_id}", headers=headers)
    assert del_res.status_code == 204
    assert client.get(f"/api/v1/production/machines/{machine_id}", headers=headers).status_code == 404


# ---------------------------------------------------------------------------
# Production Summary Tests
# ---------------------------------------------------------------------------

def test_production_summary_kpi_metrics(client: TestClient, db_session: Session):
    """Production summary endpoint returns accurate deterministic aggregations."""
    user = create_test_user(db_session, "summary_user@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user.id, "Bangle")

    # Add 2 workers (1 available 8h, 1 unavailable 6h)
    client.post(
        "/api/v1/production/workers",
        json={"name": "Worker 1", "skill": "casting", "capacity_hours_per_day": 8.0, "is_available": True},
        headers=headers,
    )
    client.post(
        "/api/v1/production/workers",
        json={"name": "Worker 2", "skill": "polishing", "capacity_hours_per_day": 6.0, "is_available": False},
        headers=headers,
    )

    # Add 2 machines (1 available 10h, 1 available 6h)
    client.post(
        "/api/v1/production/machines",
        json={"name": "Laser 1", "machine_type": "laser_engraver", "capacity_hours_per_day": 10.0, "is_available": True},
        headers=headers,
    )
    client.post(
        "/api/v1/production/machines",
        json={"name": "3D Printer", "machine_type": "3d_wax_printer", "capacity_hours_per_day": 6.0, "is_available": True},
        headers=headers,
    )

    # Add orders: 1 pending future, 1 in_progress past (overdue), 1 completed past
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    past = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()

    client.post("/api/v1/production/orders", json={"design_id": str(design.id), "quantity": 5, "status": "pending", "deadline": future}, headers=headers)
    client.post("/api/v1/production/orders", json={"design_id": str(design.id), "quantity": 10, "status": "in_progress", "deadline": past}, headers=headers)
    client.post("/api/v1/production/orders", json={"design_id": str(design.id), "quantity": 2, "status": "completed", "deadline": past}, headers=headers)

    # Fetch summary
    summary_res = client.get("/api/v1/production/summary", headers=headers)
    assert summary_res.status_code == 200
    data = summary_res.json()

    assert data["total_orders"] == 3
    assert data["pending_orders"] == 1
    assert data["in_progress_orders"] == 1
    assert data["completed_orders"] == 1
    assert data["cancelled_orders"] == 0
    assert data["overdue_orders"] == 1  # only in_progress past deadline

    assert data["total_workers"] == 2
    assert data["available_workers"] == 1
    assert data["total_worker_capacity_hours"] == 8.0

    assert data["total_machines"] == 2
    assert data["available_machines"] == 2
    assert data["total_machine_capacity_hours"] == 16.0


def test_unauthenticated_requests_rejected(client: TestClient):
    """Unauthenticated requests to all production endpoints are rejected with 401."""
    assert client.get("/api/v1/production/summary").status_code == 401
    assert client.get("/api/v1/production/orders").status_code == 401
    assert client.post("/api/v1/production/orders", json={}).status_code == 401
    assert client.get("/api/v1/production/workers").status_code == 401
    assert client.post("/api/v1/production/workers", json={}).status_code == 401
    assert client.get("/api/v1/production/machines").status_code == 401
    assert client.post("/api/v1/production/machines", json={}).status_code == 401
