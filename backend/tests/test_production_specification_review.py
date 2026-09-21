"""
Production Specification Artisan Review & Approval Test Suite (Phase I.4)
Verifies:
- Unauthenticated PATCH and approve rejected (401)
- Multi-tenant IDOR protection (404 for another user's specification)
- Editing draft specifications (materials, gemstones, steps, scalar overrides)
- Client schema forbidden fields protection (422)
- Artisan override provenance tagging (ARTISAN_OVERRIDE vs AI_ESTIMATE)
- Manufacturing readiness validation upon approval
- Successful approval transitions status to 'approved' with approved_at
- Approval of gemstone-free pieces (plain bands)
- Strict immutability once approved (409 Conflict on PATCH or duplicate approve)
"""

import uuid
from datetime import datetime, timezone
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
# Test Helpers
# ---------------------------------------------------------------------------

def create_test_user(db_session: Session, email: str = "artisan.review@jewelmind.com") -> User:
    """Creates a distinct user for testing."""
    return user_service.create(
        db_session,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Review Artisan",
        ),
    )


def get_auth_headers(user: User) -> dict:
    """Generates standard JWT authorization headers."""
    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


def create_specification_tree(
    db_session: Session,
    user: User,
    status: str = "draft",
    include_gemstones: bool = True,
) -> ProductionSpecification:
    """Creates a sample specification with material, gemstone, and routing steps."""
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Review Test Ring",
        category="ring",
        status="ready",
        ai_prompt="18k gold solitaire ring",
        rendered_image_url="https://storage.jewelmind.internal/renders/ring_v1.png",
    )
    db_session.add(design)
    db_session.commit()

    render = DesignRender(
        id=uuid.uuid4(),
        design_id=design.id,
        user_id=user.id,
        version_number=1,
        render_mode="text",
        prompt="18k gold solitaire ring",
        enhanced_prompt="An 18k gold solitaire ring with round brilliant diamond",
        image_url="https://storage.jewelmind.internal/renders/ring_v1.png",
        thumbnail_url="https://storage.jewelmind.internal/renders/ring_v1.png",
        seed=42,
        is_approved_for_production=True,
    )
    db_session.add(render)
    db_session.commit()

    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status=status,
        category="ring",
        estimated_rough_metal_weight_grams=5.5,
        estimated_finished_metal_weight_grams=4.8,
        total_gemstone_count=1 if include_gemstones else 0,
        estimated_total_bench_hours=8.5,
        complexity_rating="moderate",
        fabrication_notes="Initial AI-generated fabrication blueprint.",
        ai_confidence_score=0.88,
        approved_at=datetime.now(timezone.utc) if status == "approved" else None,
    )
    db_session.add(spec)
    db_session.commit()

    mat = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type="gold",
        metal_purity="18k",
        metal_color="yellow",
        metal_finish="high_polish",
        estimated_weight_grams=4.8,
        casting_loss_percentage=10.0,
    )
    db_session.add(mat)

    if include_gemstones:
        gem = ProductionGemstone(
            id=uuid.uuid4(),
            specification_id=spec.id,
            gemstone_type="diamond",
            cut_shape="round_brilliant",
            stone_count=1,
            estimated_carat_weight=1.0,
            approximate_dimensions_mm="6.5mm",
            setting_type="prong",
            is_center_stone=True,
        )
        db_session.add(gem)

    step1 = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=1,
        stage_name="Casting",
        required_skill="caster",
        required_machine_type="vacuum_caster",
        base_hours=2.0,
        per_unit_hours=0.5,
        description="Vacuum investment casting in 18k yellow gold.",
        quality_checkpoint="Check for casting porosity.",
    )
    step2 = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=2,
        stage_name="Stone Setting",
        required_skill="setter",
        required_machine_type="microscope_bench",
        base_hours=4.0,
        per_unit_hours=1.0,
        description="Set 1.0ct center stone in 4-prong head.",
        quality_checkpoint="Verify prong symmetry and tightness.",
    )
    db_session.add(step1)
    db_session.add(step2)
    db_session.commit()
    db_session.refresh(spec)
    return spec


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_unauthenticated_patch_and_approve_rejected(client: TestClient, db_session: Session):
    """Verifies that unauthenticated PATCH and POST /approve requests return 401."""
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user)

    # PATCH unauthenticated
    patch_res = client.patch(
        f"/api/v1/production-specifications/{spec.id}",
        json={"category": "earrings"},
    )
    assert patch_res.status_code == 401

    # POST /approve unauthenticated
    approve_res = client.post(
        f"/api/v1/production-specifications/{spec.id}/approve"
    )
    assert approve_res.status_code == 401


def test_multi_tenant_idor_protection(client: TestClient, db_session: Session):
    """Verifies that User B cannot edit or approve User A's specification (returns 404)."""
    user_a = create_test_user(db_session, email=f"user_a_{uuid.uuid4().hex[:6]}@jewelmind.com")
    user_b = create_test_user(db_session, email=f"user_b_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec_a = create_specification_tree(db_session, user_a)

    headers_b = get_auth_headers(user_b)

    # User B attempts to PATCH spec_a
    patch_res = client.patch(
        f"/api/v1/production-specifications/{spec_a.id}",
        headers=headers_b,
        json={"category": "pendant"},
    )
    assert patch_res.status_code == 404
    assert "not found" in patch_res.json()["detail"].lower()

    # User B attempts to approve spec_a
    approve_res = client.post(
        f"/api/v1/production-specifications/{spec_a.id}/approve",
        headers=headers_b,
    )
    assert approve_res.status_code == 404
    assert "not found" in approve_res.json()["detail"].lower()


def test_patch_draft_specification_scalars(client: TestClient, db_session: Session):
    """Verifies updating scalar fields of a draft specification."""
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user)
    headers = get_auth_headers(user)

    payload = {
        "category": "necklace",
        "estimated_rough_metal_weight_grams": 7.2,
        "estimated_finished_metal_weight_grams": 6.5,
        "complexity_rating": "intricate",
        "fabrication_notes": "Artisan updated: reinforce pendant bail.",
    }

    res = client.patch(
        f"/api/v1/production-specifications/{spec.id}",
        headers=headers,
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "necklace"
    assert data["estimated_rough_metal_weight_grams"] == 7.2
    assert data["estimated_finished_metal_weight_grams"] == 6.5
    assert data["complexity_rating"] == "intricate"
    assert "reinforce pendant bail" in data["fabrication_notes"]


def test_patch_materials_and_provenance_tagging(client: TestClient, db_session: Session):
    """
    Verifies updating existing material, adding a new material, and deleting omitted.
    Verifies that overridden/new items receive origin='ARTISAN_OVERRIDE'.
    """
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user)
    headers = get_auth_headers(user)

    existing_mat = spec.materials[0]

    payload = {
        "materials": [
            # 1. Update existing material
            {
                "id": str(existing_mat.id),
                "metal_type": "platinum",
                "metal_purity": "950",
                "metal_color": "white",
                "metal_finish": "satin",
                "estimated_weight_grams": 6.0,
                "casting_loss_percentage": 12.0,
            },
            # 2. Add brand new material (e.g. solder or accent gold)
            {
                "metal_type": "gold",
                "metal_purity": "18k",
                "metal_color": "yellow",
                "estimated_weight_grams": 0.5,
                "casting_loss_percentage": 5.0,
            },
        ]
    }

    res = client.patch(
        f"/api/v1/production-specifications/{spec.id}",
        headers=headers,
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["materials"]) == 2

    # Both should have ARTISAN_OVERRIDE origin
    for mat in data["materials"]:
        assert mat["origin"] == "ARTISAN_OVERRIDE"

    # Verify existing item was updated
    updated_mat = next(m for m in data["materials"] if m["id"] == str(existing_mat.id))
    assert updated_mat["metal_type"] == "platinum"
    assert updated_mat["metal_purity"] == "950"
    assert updated_mat["metal_finish"] == "satin"

    # Verify untouched step still has origin='AI_ESTIMATE'
    assert len(data["steps"]) == 2
    for step in data["steps"]:
        assert step["origin"] == "AI_ESTIMATE"


def test_patch_gemstones_reconciliation_and_removal(client: TestClient, db_session: Session):
    """Verifies modifying gemstones and removing all gemstones for plain jewellery."""
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user, include_gemstones=True)
    headers = get_auth_headers(user)

    assert len(spec.gemstones) == 1

    # Remove all gemstones (e.g. converting to a plain gold band)
    payload = {
        "gemstones": [],
        "total_gemstone_count": 0,
    }

    res = client.patch(
        f"/api/v1/production-specifications/{spec.id}",
        headers=headers,
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["gemstones"]) == 0
    assert data["total_gemstone_count"] == 0


def test_patch_steps_reconciliation(client: TestClient, db_session: Session):
    """Verifies adding, updating, and removing manufacturing routing steps."""
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user)
    headers = get_auth_headers(user)

    existing_step1 = spec.steps[0]

    payload = {
        "steps": [
            # Keep and update Step 1
            {
                "id": str(existing_step1.id),
                "step_number": 1,
                "stage_name": "Precision Laser Sintering",
                "required_skill": "cad_cam_technician",
                "required_machine_type": "dmls_printer",
                "base_hours": 3.0,
                "per_unit_hours": 0.5,
                "description": "Additive manufacturing of ring matrix.",
            },
            # Add Step 2 (Polishing, replacing old stone setting)
            {
                "step_number": 2,
                "stage_name": "Final Hand Polishing",
                "required_skill": "polisher",
                "required_machine_type": "polishing_lathe",
                "base_hours": 1.5,
                "per_unit_hours": 0.5,
                "description": "High polish finish using rouge.",
            },
        ]
    }

    res = client.patch(
        f"/api/v1/production-specifications/{spec.id}",
        headers=headers,
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["steps"]) == 2
    assert data["steps"][0]["stage_name"] == "Precision Laser Sintering"
    assert data["steps"][1]["stage_name"] == "Final Hand Polishing"
    assert data["steps"][0]["origin"] == "ARTISAN_OVERRIDE"
    assert data["steps"][1]["origin"] == "ARTISAN_OVERRIDE"


def test_patch_rejects_client_injected_forbidden_fields(client: TestClient, db_session: Session):
    """Verifies that client cannot inject server-controlled fields like status, id, user_id."""
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user)
    headers = get_auth_headers(user)

    # Attempt to bypass approval by passing status='approved' directly in PATCH
    res = client.patch(
        f"/api/v1/production-specifications/{spec.id}",
        headers=headers,
        json={"status": "approved"},
    )
    # Pydantic extra="forbid" raises 422 Unprocessable Entity
    assert res.status_code == 422

    # Attempt to alter user_id
    res = client.patch(
        f"/api/v1/production-specifications/{spec.id}",
        headers=headers,
        json={"user_id": str(uuid.uuid4())},
    )
    assert res.status_code == 422

    # Attempt to alter render_id
    res = client.patch(
        f"/api/v1/production-specifications/{spec.id}",
        headers=headers,
        json={"render_id": str(uuid.uuid4())},
    )
    assert res.status_code == 422


def test_approve_valid_draft_specification(client: TestClient, db_session: Session):
    """Verifies that approving a valid draft transitions status to 'approved'."""
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user)
    headers = get_auth_headers(user)

    assert spec.status == "draft"
    assert spec.approved_at is None

    res = client.post(
        f"/api/v1/production-specifications/{spec.id}/approve",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"
    assert data["approved_at"] is not None


def test_approve_gemstone_free_piece_success(client: TestClient, db_session: Session):
    """Verifies that plain pieces (e.g. plain wedding bands) approve cleanly without gemstones."""
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user, include_gemstones=False)
    headers = get_auth_headers(user)

    res = client.post(
        f"/api/v1/production-specifications/{spec.id}/approve",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"
    assert data["total_gemstone_count"] == 0
    assert len(data["gemstones"]) == 0


def test_approve_validation_failure_empty_materials(client: TestClient, db_session: Session):
    """Verifies that a specification with 0 materials cannot be approved (400 Bad Request)."""
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user)
    headers = get_auth_headers(user)

    # Remove all materials via direct DB edit
    for m in list(spec.materials):
        db_session.delete(m)
    db_session.commit()
    db_session.refresh(spec)

    res = client.post(
        f"/api/v1/production-specifications/{spec.id}/approve",
        headers=headers,
    )
    assert res.status_code == 400
    assert "at least one material" in res.json()["detail"].lower()


def test_approve_validation_failure_empty_steps(client: TestClient, db_session: Session):
    """Verifies that a specification with 0 routing steps cannot be approved (400 Bad Request)."""
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user)
    headers = get_auth_headers(user)

    # Remove all steps via direct DB edit
    for s in list(spec.steps):
        db_session.delete(s)
    db_session.commit()
    db_session.refresh(spec)

    res = client.post(
        f"/api/v1/production-specifications/{spec.id}/approve",
        headers=headers,
    )
    assert res.status_code == 400
    assert "routing stage" in res.json()["detail"].lower()


def test_approve_validation_failure_non_sequential_steps(client: TestClient, db_session: Session):
    """Verifies that non-sequential step numbers (e.g. step 1 then step 3) fail validation."""
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user)
    headers = get_auth_headers(user)

    # Set steps to non-sequential (1 and 3)
    spec.steps[1].step_number = 3
    db_session.commit()

    res = client.post(
        f"/api/v1/production-specifications/{spec.id}/approve",
        headers=headers,
    )
    assert res.status_code == 400
    assert "sequential" in res.json()["detail"].lower()


def test_immutability_of_approved_specification(client: TestClient, db_session: Session):
    """
    Verifies that once a specification is approved:
    1. Direct PATCH requests return 409 Conflict.
    2. Re-approving returns 409 Conflict.
    """
    user = create_test_user(db_session, email=f"user_{uuid.uuid4().hex[:6]}@jewelmind.com")
    spec = create_specification_tree(db_session, user, status="approved")
    headers = get_auth_headers(user)

    # Attempt to edit approved spec
    patch_res = client.patch(
        f"/api/v1/production-specifications/{spec.id}",
        headers=headers,
        json={"category": "earrings"},
    )
    assert patch_res.status_code == 409
    assert "approved" in patch_res.json()["detail"].lower()
    assert "immutable" in patch_res.json()["detail"].lower()

    # Attempt to re-approve already approved spec
    approve_res = client.post(
        f"/api/v1/production-specifications/{spec.id}/approve",
        headers=headers,
    )
    assert approve_res.status_code == 409
    assert "already approved" in approve_res.json()["detail"].lower()

