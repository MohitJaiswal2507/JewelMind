"""
Production Specification API Integration & Security Test Suite (Phase I.3)
Verifies authentication, multi-tenant IDOR protection, referential integrity,
monotonic versioning, nested BOM persistence, transaction rollbacks, and fallback behavior.
"""

import uuid
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.design import Design, DesignRender
from app.models.specification import (
    ProductionGemstone,
    ProductionMaterial,
    ProductionSpecification,
    ProductionStep,
)
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.user_service import user_service


# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

def create_test_user(db: Session, email: str = "artisan.phase_i3@jewelmind.com") -> User:
    """Creates a distinct authenticated user for testing."""
    return user_service.create(
        db,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Phase I.3 Artisan",
        ),
    )


def get_auth_headers(user: User) -> dict:
    """Generates standard JWT bearer authorization headers."""
    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


def create_test_design(
    db: Session,
    user: User,
    category: str = "ring",
    name: str = "Solitaire Engagement Ring",
) -> Design:
    """Creates a parent Design record."""
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name=name,
        category=category,
        status="ready",
        ai_prompt="18k white gold ring with 1ct diamond",
        rendered_image_url="https://storage.jewelmind.internal/renders/ring_v1.png",
    )
    db.add(design)
    db.commit()
    db.refresh(design)
    return design


def create_test_render(
    db: Session,
    design: Design,
    user: User,
    version: int = 1,
    image_url: str = "https://storage.jewelmind.internal/renders/ring_v1.png",
    is_approved: bool = True,
) -> DesignRender:
    """Creates an approved DesignRender version record."""
    render = DesignRender(
        id=uuid.uuid4(),
        design_id=design.id,
        user_id=user.id,
        version_number=version,
        render_mode="text",
        prompt="18k white gold ring with 1ct diamond",
        enhanced_prompt="A luxury 18k white gold solitaire engagement ring with 1.0ct round brilliant diamond center stone",
        structured_state={
            "material": {"metal": "gold", "purity": "18k", "color": "white"},
            "gemstones": [{"gemstone_type": "diamond", "cut": "round"}],
        },
        image_url=image_url,
        thumbnail_url=image_url,
        control_type="none",
        control_strength=0.0,
        seed=100 + version,
        is_approved_for_production=is_approved,
    )
    db.add(render)
    db.commit()
    db.refresh(render)
    return render


# ===========================================================================
# A. Authentication Enforcement Tests
# ===========================================================================

def test_generate_unauthenticated_rejected(client: TestClient):
    """POST /generate without credentials must return HTTP 401."""
    res = client.post(
        "/api/v1/production-specifications/generate",
        json={"render_id": str(uuid.uuid4())},
    )
    assert res.status_code == 401


def test_get_specification_unauthenticated_rejected(client: TestClient):
    """GET /{specification_id} without credentials must return HTTP 401."""
    res = client.get(f"/api/v1/production-specifications/{uuid.uuid4()}")
    assert res.status_code == 401


def test_get_by_render_unauthenticated_rejected(client: TestClient):
    """GET /by-render/{render_id} without credentials must return HTTP 401."""
    res = client.get(f"/api/v1/production-specifications/by-render/{uuid.uuid4()}")
    assert res.status_code == 401


# ===========================================================================
# B. Ownership & IDOR Protection Tests
# ===========================================================================

def test_generate_own_render_success(client: TestClient, db_session: Session):
    """Authenticated user successfully generates specification from their own render."""
    user = create_test_user(db_session, "artisan.alice@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user, category="ring")
    render = create_test_render(db_session, design, user, version=1)

    res = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers,
        json={"render_id": str(render.id)},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["design_id"] == str(design.id)
    assert data["render_id"] == str(render.id)
    assert data["user_id"] == str(user.id)
    assert data["version_number"] == 1
    assert data["status"] == "draft"


def test_generate_other_user_render_rejected_404(client: TestClient, db_session: Session):
    """User B cannot generate specification from User A's render (IDOR safe: 404)."""
    user_a = create_test_user(db_session, "user_a.idor1@jewelmind.com")
    user_b = create_test_user(db_session, "user_b.idor1@jewelmind.com")
    headers_b = get_auth_headers(user_b)

    design_a = create_test_design(db_session, user_a)
    render_a = create_test_render(db_session, design_a, user_a)

    res = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers_b,
        json={"render_id": str(render_a.id)},
    )
    assert res.status_code == 404
    assert "not found or access denied" in res.json()["detail"].lower()


def test_get_specification_other_user_rejected_404(client: TestClient, db_session: Session):
    """User B cannot view User A's specification by ID (IDOR safe: 404)."""
    user_a = create_test_user(db_session, "user_a.idor2@jewelmind.com")
    user_b = create_test_user(db_session, "user_b.idor2@jewelmind.com")
    headers_a = get_auth_headers(user_a)
    headers_b = get_auth_headers(user_b)

    design_a = create_test_design(db_session, user_a)
    render_a = create_test_render(db_session, design_a, user_a)

    # User A creates spec
    gen_res = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers_a,
        json={"render_id": str(render_a.id)},
    )
    assert gen_res.status_code == 201
    spec_id = gen_res.json()["id"]

    # User B attempts to access it
    res_b = client.get(
        f"/api/v1/production-specifications/{spec_id}",
        headers=headers_b,
    )
    assert res_b.status_code == 404
    assert "not found or access denied" in res_b.json()["detail"].lower()


def test_get_by_render_other_user_rejected_404(client: TestClient, db_session: Session):
    """User B cannot view specifications for User A's render version (IDOR safe: 404)."""
    user_a = create_test_user(db_session, "user_a.idor3@jewelmind.com")
    user_b = create_test_user(db_session, "user_b.idor3@jewelmind.com")
    headers_a = get_auth_headers(user_a)
    headers_b = get_auth_headers(user_b)

    design_a = create_test_design(db_session, user_a)
    render_a = create_test_render(db_session, design_a, user_a)

    # User A creates spec
    client.post(
        "/api/v1/production-specifications/generate",
        headers=headers_a,
        json={"render_id": str(render_a.id)},
    )

    # User B queries by render_id
    res_b = client.get(
        f"/api/v1/production-specifications/by-render/{render_a.id}",
        headers=headers_b,
    )
    assert res_b.status_code == 404


# ===========================================================================
# C. Referential Integrity & Validation Tests
# ===========================================================================

def test_generate_with_empty_image_url_rejected(client: TestClient, db_session: Session):
    """Render without a valid image URL cannot be used to generate a specification."""
    user = create_test_user(db_session, "user.noimage@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    render = create_test_render(db_session, design, user, image_url="")

    res = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers,
        json={"render_id": str(render.id)},
    )
    assert res.status_code == 400
    assert "image url" in res.json()["detail"].lower()


def test_generate_disallows_extra_client_fields(client: TestClient, db_session: Session):
    """Client attempting to inject server-controlled fields (e.g. user_id, version_number) is rejected (422)."""
    user = create_test_user(db_session, "user.extra_fields@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    render = create_test_render(db_session, design, user)

    res = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers,
        json={
            "render_id": str(render.id),
            "version_number": 99,  # Illegal extra field
            "status": "approved",  # Illegal extra field
        },
    )
    assert res.status_code == 422


# ===========================================================================
# D. Monotonic Versioning Tests
# ===========================================================================

def test_monotonic_versioning_increments(client: TestClient, db_session: Session):
    """
    Generating specifications for the same design produces incrementing version numbers
    (v1, then v2), while preserving all historical versions.
    """
    user = create_test_user(db_session, "artisan.versions@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user, category="necklace")
    render = create_test_render(db_session, design, user, version=1)

    # 1. First generation -> v1
    res1 = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers,
        json={"render_id": str(render.id)},
    )
    assert res1.status_code == 201
    spec1 = res1.json()
    assert spec1["version_number"] == 1
    spec1_id = spec1["id"]

    # 2. Second generation -> v2
    res2 = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers,
        json={"render_id": str(render.id), "material_hint": "18k rose gold"},
    )
    assert res2.status_code == 201
    spec2 = res2.json()
    assert spec2["version_number"] == 2
    spec2_id = spec2["id"]
    assert spec1_id != spec2_id

    # 3. Verify both versions exist and are queryable
    check1 = client.get(f"/api/v1/production-specifications/{spec1_id}", headers=headers)
    assert check1.status_code == 200
    assert check1.json()["version_number"] == 1

    check2 = client.get(f"/api/v1/production-specifications/{spec2_id}", headers=headers)
    assert check2.status_code == 200
    assert check2.json()["version_number"] == 2

    # 4. Verify by-render history returns both (newest first)
    hist_res = client.get(
        f"/api/v1/production-specifications/by-render/{render.id}",
        headers=headers,
    )
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) == 2
    assert hist[0]["version_number"] == 2
    assert hist[1]["version_number"] == 1


def test_multiple_renders_same_design_distinct_lineage(client: TestClient, db_session: Session):
    """
    Two different render versions of the same design track separate specifications
    while sharing the monotonic design versioning counter.
    """
    user = create_test_user(db_session, "artisan.multirender@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user, category="earring")
    render_v1 = create_test_render(db_session, design, user, version=1)
    render_v2 = create_test_render(db_session, design, user, version=2)

    # Spec for Render V1 -> Design Spec v1
    res1 = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers,
        json={"render_id": str(render_v1.id)},
    )
    assert res1.status_code == 201
    assert res1.json()["version_number"] == 1
    assert res1.json()["render_id"] == str(render_v1.id)

    # Spec for Render V2 -> Design Spec v2
    res2 = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers,
        json={"render_id": str(render_v2.id)},
    )
    assert res2.status_code == 201
    assert res2.json()["version_number"] == 2
    assert res2.json()["render_id"] == str(render_v2.id)

    # History for Render V1 has 1 spec
    hist_v1 = client.get(
        f"/api/v1/production-specifications/by-render/{render_v1.id}",
        headers=headers,
    ).json()
    assert len(hist_v1) == 1
    assert hist_v1[0]["render_id"] == str(render_v1.id)

    # History for Render V2 has 1 spec
    hist_v2 = client.get(
        f"/api/v1/production-specifications/by-render/{render_v2.id}",
        headers=headers,
    ).json()
    assert len(hist_v2) == 1
    assert hist_v2[0]["render_id"] == str(render_v2.id)


# ===========================================================================
# E. Persistence & Child BOM Verification Tests
# ===========================================================================

def test_nested_bom_and_routing_persisted_correctly(client: TestClient, db_session: Session):
    """
    Verifies that materials, gemstones, and routing steps are all populated in DB
    and returned in the API response.
    """
    user = create_test_user(db_session, "artisan.bom@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user, category="ring")
    render = create_test_render(db_session, design, user)

    res = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers,
        json={
            "render_id": str(render.id),
            "user_prompt": "18k white gold solitaire ring with 1ct round diamond",
        },
    )
    assert res.status_code == 201
    data = res.json()

    # Materials
    assert len(data["materials"]) >= 1
    mat = data["materials"][0]
    assert mat["specification_id"] == data["id"]
    assert mat["metal_type"] == "gold"
    assert mat["metal_purity"] == "18k"
    assert mat["metal_color"] == "white"
    assert mat["estimated_weight_grams"] > 0

    # Gemstones
    assert len(data["gemstones"]) >= 1
    gem = data["gemstones"][0]
    assert gem["specification_id"] == data["id"]
    assert gem["gemstone_type"] == "diamond"
    assert gem["stone_count"] >= 1

    # Steps
    assert len(data["steps"]) >= 4
    step1 = data["steps"][0]
    assert step1["specification_id"] == data["id"]
    assert step1["step_number"] == 1
    assert step1["required_skill"] in ("cad_design", "casting", "polishing", "general")
    assert step1["base_hours"] >= 0


# ===========================================================================
# F. Transaction Safety & Rollback Tests
# ===========================================================================

def test_transaction_rollback_on_persistence_failure(client: TestClient, db_session: Session):
    """
    If an unexpected error or integrity conflict occurs during database commit,
    the entire transaction is rolled back and no partial specification is persisted.
    """
    user = create_test_user(db_session, "artisan.rollback@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    render = create_test_render(db_session, design, user)

    # Count specifications before
    count_before = db_session.query(ProductionSpecification).filter_by(user_id=user.id).count()

    # Simulate database failure during commit
    with patch.object(Session, "commit", side_effect=Exception("Simulated DB connection failure")):
        res = client.post(
            "/api/v1/production-specifications/generate",
            headers=headers,
            json={"render_id": str(render.id)},
        )
        assert res.status_code == 500

    # Verify zero specifications were created
    count_after = db_session.query(ProductionSpecification).filter_by(user_id=user.id).count()
    assert count_after == count_before


# ===========================================================================
# G. AI Fallback & Status Tests
# ===========================================================================

def test_generate_deterministic_fallback_persists_valid_specification(client: TestClient, db_session: Session):
    """
    When Gemini API is unavailable, the service engages deterministic fallback
    and persists a fully usable Production Specification.
    """
    user = create_test_user(db_session, "artisan.fallback@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user, category="bracelet")
    render = create_test_render(db_session, design, user)

    # Simulate Gemini unavailable
    with patch("app.services.gemini_production_service.GeminiProductionService.is_available", return_value=False):
        res = client.post(
            "/api/v1/production-specifications/generate",
            headers=headers,
            json={"render_id": str(render.id)},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["category"] == "bracelet"
        assert len(data["materials"]) >= 1
        assert len(data["steps"]) >= 4
        assert data["status"] == "draft"  # Initial state is strictly draft


def test_initial_status_is_draft_not_approved(client: TestClient, db_session: Session):
    """Generated specifications must always initialize in 'draft' status (never 'approved')."""
    user = create_test_user(db_session, "artisan.status@jewelmind.com")
    headers = get_auth_headers(user)
    design = create_test_design(db_session, user)
    render = create_test_render(db_session, design, user)

    res = client.post(
        "/api/v1/production-specifications/generate",
        headers=headers,
        json={"render_id": str(render.id)},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "draft"
    assert res.json()["approved_at"] is None
