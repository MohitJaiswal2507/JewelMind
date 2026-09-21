"""
Phase H: Studio & Render History Comprehensive Test Suite
Tests for persistent render versioning, lineage tracking, approval mechanics,
production order protection, and Lookbook integration.
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User
from app.models.design import Design, DesignRender
from app.models.production import ProductionOrder
from app.services.user_service import user_service
from app.schemas.auth import UserCreate


def create_test_user(db: Session, email: str = "artisan.phase_h@jewelmind.com") -> User:
    """Helper to create an authenticated test user."""
    return user_service.create(
        db,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Phase H Artisan",
        ),
    )


def get_auth_headers(user: User) -> dict:
    """Helper to generate JWT Bearer headers."""
    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


def create_test_design(db: Session, user: User, name: str = "Filigree Necklace") -> Design:
    """Helper to create a test design in DB."""
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name=name,
        category="Necklace",
        status="ready",
        ai_prompt="18k gold intricate necklace",
        rendered_image_url="https://storage.jewelmind.internal/renders/initial.png",
    )
    db.add(design)
    db.commit()
    db.refresh(design)
    return design


def create_test_render(
    db: Session,
    design: Design,
    user: User,
    version: int,
    image_url: str,
    render_mode: str = "text",
    is_approved: bool = False,
    parent_render_id: uuid.UUID = None,
) -> DesignRender:
    """Helper to create a test DesignRender in DB."""
    render = DesignRender(
        id=uuid.uuid4(),
        design_id=design.id,
        user_id=user.id,
        version_number=version,
        parent_render_id=parent_render_id,
        render_mode=render_mode,
        prompt=f"Render prompt for version {version}",
        image_url=image_url,
        thumbnail_url=image_url,
        control_type="lineart" if render_mode == "doodle" else "none",
        control_strength=0.65 if render_mode == "doodle" else 0.0,
        seed=42 + version,
        is_approved_for_production=is_approved,
    )
    db.add(render)
    db.commit()
    db.refresh(render)
    return render


# ==============================================================================
# 1. Render History Retrieval Endpoint Tests
# ==============================================================================

def test_get_design_renders_empty(client: TestClient, db_session: Session):
    """GET /designs/{id}/renders returns empty list if no renders exist."""
    user = create_test_user(db_session, "user.renders1@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)

    res = client.get(f"/api/v1/designs/{design.id}/renders", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["renders"] == []


def test_get_design_renders_chronological_ordering(client: TestClient, db_session: Session):
    """GET /designs/{id}/renders returns renders ordered chronologically by version ascending."""
    user = create_test_user(db_session, "user.renders2@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)

    # Insert out of order
    r2 = create_test_render(db_session, design, user, version=2, image_url="https://url/v2.png")
    r1 = create_test_render(db_session, design, user, version=1, image_url="https://url/v1.png")
    r3 = create_test_render(db_session, design, user, version=3, image_url="https://url/v3.png")

    res = client.get(f"/api/v1/designs/{design.id}/renders", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["renders"]) == 3
    assert data["renders"][0]["version_number"] == 1
    assert data["renders"][1]["version_number"] == 2
    assert data["renders"][2]["version_number"] == 3


def test_get_design_renders_cross_user_isolation(client: TestClient, db_session: Session):
    """User B cannot view User A's design renders."""
    user_a = create_test_user(db_session, "user.a.renders@jewelmind.com")
    user_b = create_test_user(db_session, "user.b.renders@jewelmind.com")
    headers_b = get_auth_headers(user_b)
    design_a = create_test_design(db_session, user_a)
    create_test_render(db_session, design_a, user_a, version=1, image_url="https://url/v1.png")

    res = client.get(f"/api/v1/designs/{design_a.id}/renders", headers=headers_b)
    assert res.status_code == 404


def test_get_design_renders_unauthenticated(client: TestClient, db_session: Session):
    """Unauthenticated request is rejected with 401."""
    user = create_test_user(db_session, "user.noauth@jewelmind.com")
    design = create_test_design(db_session, user)

    res = client.get(f"/api/v1/designs/{design.id}/renders")
    assert res.status_code == 401


# ==============================================================================
# 2. Render Approval Endpoint Tests
# ==============================================================================

def test_approve_design_render_success(client: TestClient, db_session: Session):
    """Approving a render sets is_approved=True and updates design.rendered_image_url."""
    user = create_test_user(db_session, "user.approve1@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    r1 = create_test_render(db_session, design, user, version=1, image_url="https://url/v1.png")

    res = client.post(f"/api/v1/designs/{design.id}/renders/{r1.id}/approve", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(r1.id)
    assert data["is_approved_for_production"] is True

    # Verify DB state
    db_session.refresh(design)
    db_session.refresh(r1)
    assert r1.is_approved_for_production is True
    assert design.rendered_image_url == "https://url/v1.png"


def test_approve_design_render_atomically_unapproves_siblings(client: TestClient, db_session: Session):
    """Approving V2 unapproves previously approved V1 atomically."""
    user = create_test_user(db_session, "user.approve2@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    r1 = create_test_render(db_session, design, user, version=1, image_url="https://url/v1.png", is_approved=True)
    r2 = create_test_render(db_session, design, user, version=2, image_url="https://url/v2.png", is_approved=False)

    res = client.post(f"/api/v1/designs/{design.id}/renders/{r2.id}/approve", headers=headers)
    assert res.status_code == 200
    assert res.json()["is_approved_for_production"] is True

    db_session.refresh(r1)
    db_session.refresh(r2)
    db_session.refresh(design)
    assert r1.is_approved_for_production is False
    assert r2.is_approved_for_production is True
    assert design.rendered_image_url == "https://url/v2.png"


def test_approve_design_render_not_found(client: TestClient, db_session: Session):
    """Approving a non-existent render returns 404."""
    user = create_test_user(db_session, "user.approve404@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    fake_id = uuid.uuid4()

    res = client.post(f"/api/v1/designs/{design.id}/renders/{fake_id}/approve", headers=headers)
    assert res.status_code == 404


def test_approve_design_render_cross_user(client: TestClient, db_session: Session):
    """User B cannot approve User A's render."""
    user_a = create_test_user(db_session, "user.a.appr@jewelmind.com")
    user_b = create_test_user(db_session, "user.b.appr@jewelmind.com")
    headers_b = get_auth_headers(user_b)
    design_a = create_test_design(db_session, user_a)
    r1 = create_test_render(db_session, design_a, user_a, version=1, image_url="https://url/v1.png")

    res = client.post(f"/api/v1/designs/{design_a.id}/renders/{r1.id}/approve", headers=headers_b)
    assert res.status_code == 404


# ==============================================================================
# 3. Render Deletion & Fallback Endpoint Tests
# ==============================================================================

def test_delete_design_render_success_updates_fallback(client: TestClient, db_session: Session):
    """Deleting active render V2 updates design.rendered_image_url to latest remaining (V1)."""
    user = create_test_user(db_session, "user.del1@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    r1 = create_test_render(db_session, design, user, version=1, image_url="https://url/v1.png")
    r2 = create_test_render(db_session, design, user, version=2, image_url="https://url/v2.png")
    design.rendered_image_url = "https://url/v2.png"
    db_session.add(design)
    db_session.commit()

    res = client.delete(f"/api/v1/designs/{design.id}/renders/{r2.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    db_session.refresh(design)
    assert design.rendered_image_url == "https://url/v1.png"
    assert db_session.query(DesignRender).filter(DesignRender.id == r2.id).first() is None


def test_delete_design_render_last_remaining_sets_none(client: TestClient, db_session: Session):
    """Deleting the last remaining render sets design.rendered_image_url to None."""
    user = create_test_user(db_session, "user.del_last@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    r1 = create_test_render(db_session, design, user, version=1, image_url="https://url/v1.png")
    design.rendered_image_url = "https://url/v1.png"
    db_session.add(design)
    db_session.commit()

    res = client.delete(f"/api/v1/designs/{design.id}/renders/{r1.id}", headers=headers)
    assert res.status_code == 200

    db_session.refresh(design)
    assert design.rendered_image_url is None
    assert db_session.query(DesignRender).filter(DesignRender.id == r1.id).first() is None


def test_delete_design_render_blocked_by_active_production_order(client: TestClient, db_session: Session):
    """Deleting a render assigned to a production order returns HTTP 409 Conflict."""
    user = create_test_user(db_session, "user.prod_prot@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    r1 = create_test_render(db_session, design, user, version=1, image_url="https://url/v1.png", is_approved=True)

    # Link to a production order
    order = ProductionOrder(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=r1.id,
        approved_render_url=r1.image_url,
        quantity=5,
        priority="high",
        status="in_progress",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(order)
    db_session.commit()

    res = client.delete(f"/api/v1/designs/{design.id}/renders/{r1.id}", headers=headers)
    assert res.status_code == 409
    assert "assigned to a production order" in res.json()["detail"]

    # Verify render is still preserved
    assert db_session.query(DesignRender).filter(DesignRender.id == r1.id).first() is not None


# ==============================================================================
# 4. Production Order Integration Tests
# ==============================================================================

def test_production_order_stores_render_id_and_url(client: TestClient, db_session: Session):
    """POST /api/v1/production/orders correctly records render_id and approved_render_url."""
    user = create_test_user(db_session, "user.prod_order@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    r1 = create_test_render(db_session, design, user, version=1, image_url="https://url/v1.png", is_approved=True)

    order_payload = {
        "design_id": str(design.id),
        "render_id": str(r1.id),
        "quantity": 10,
        "priority": "urgent",
        "status": "pending",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
        "notes": "Handcraft using approved render V1",
    }

    res = client.post("/api/v1/production/orders", json=order_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["render_id"] == str(r1.id)
    assert data["approved_render_url"] == "https://url/v1.png"


# ==============================================================================
# 5. Schema & Relationship Verification
# ==============================================================================

def test_design_list_response_includes_renders(client: TestClient, db_session: Session):
    """GET /api/v1/designs items contain renders list for lookbook consumption."""
    user = create_test_user(db_session, "user.lookbook@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    r1 = create_test_render(db_session, design, user, version=1, image_url="https://url/v1.png")
    r2 = create_test_render(db_session, design, user, version=2, image_url="https://url/v2.png")

    res = client.get("/api/v1/designs", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    target = next((item for item in items if item["id"] == str(design.id)), None)
    assert target is not None
    assert "renders" in target
    assert len(target["renders"]) == 2
    assert target["renders"][0]["version_number"] == 1
    assert target["renders"][1]["version_number"] == 2


def test_design_deletion_cascades_renders(db_session: Session):
    """Deleting a design cascades delete to all associated DesignRender rows."""
    user = create_test_user(db_session, "user.cascade@jewelmind.com")
    design = create_test_design(db_session, user)
    r1 = create_test_render(db_session, design, user, version=1, image_url="https://url/v1.png")
    r2 = create_test_render(db_session, design, user, version=2, image_url="https://url/v2.png")

    db_session.delete(design)
    db_session.commit()

    assert db_session.query(DesignRender).filter(DesignRender.design_id == design.id).count() == 0
