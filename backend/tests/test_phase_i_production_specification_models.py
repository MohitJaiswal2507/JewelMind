"""
Phase I.1: Production Specification Data Model & Migration Test Suite
Tests for ProductionSpecification, ProductionMaterial, ProductionGemstone, ProductionStep models,
foreign key cascades, version uniqueness, ON DELETE RESTRICT on DesignRender, check constraints,
and backward-compatible ProductionOrder linkage.
"""

import uuid
from datetime import datetime, timezone
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.design import Design, DesignRender
from app.models.production import ProductionOrder
from app.models.specification import (
    ProductionGemstone,
    ProductionMaterial,
    ProductionSpecification,
    ProductionStep,
)
from app.models.user import User
from app.schemas.auth import UserCreate
from app.schemas.production import (
    OrderPriority,
    OrderStatus,
    ProductionOrderCreate,
    ProductionOrderUpdate,
)
from app.services.production_service import production_service
from app.services.user_service import user_service


# ==============================================================================
# Helpers & Fixtures
# ==============================================================================

@pytest.fixture(autouse=True)
def enable_sqlite_foreign_keys(db_session: Session):
    """Ensure SQLite enforces foreign keys and check constraints during tests."""
    try:
        db_session.execute(sa.text("PRAGMA foreign_keys = ON;"))
    except Exception:
        pass
    yield


def create_user(db: Session, email: str = "artisan.phase_i1@jewelmind.com") -> User:
    return user_service.create(
        db,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Phase I Artisan",
        ),
    )


def create_design(db: Session, user: User, name: str = "Emerald Solitaire Ring", category: str = "ring") -> Design:
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name=name,
        category=category,
        status="ready",
        ai_prompt="18k gold ring with emerald",
        rendered_image_url="https://storage.jewelmind.internal/renders/v1.png",
    )
    db.add(design)
    db.commit()
    db.refresh(design)
    return design


def create_render(
    db: Session,
    design: Design,
    user: User,
    version: int = 1,
    image_url: str = "https://storage.jewelmind.internal/renders/v1.png",
    is_approved: bool = True,
) -> DesignRender:
    render = DesignRender(
        id=uuid.uuid4(),
        design_id=design.id,
        user_id=user.id,
        version_number=version,
        render_mode="text",
        prompt=f"Render prompt v{version}",
        image_url=image_url,
        thumbnail_url=image_url,
        control_type="none",
        control_strength=0.0,
        is_approved_for_production=is_approved,
    )
    db.add(render)
    db.commit()
    db.refresh(render)
    return render


# ==============================================================================
# Model Creation & Field Validation Tests
# ==============================================================================

def test_production_specification_creation(db_session: Session):
    """Test 1: Verify ProductionSpecification creation and field persistence."""
    user = create_user(db_session, "spec.create@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user, version=1)

    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
        estimated_rough_metal_weight_grams=6.5,
        estimated_finished_metal_weight_grams=5.8,
        total_gemstone_count=1,
        estimated_total_bench_hours=4.5,
        complexity_rating="moderate",
        fabrication_notes="Cast in two pieces: shank and center collet.",
        ai_confidence_score=0.92,
        approved_at=None,
    )
    db_session.add(spec)
    db_session.commit()
    db_session.refresh(spec)

    assert spec.id is not None
    assert spec.version_number == 1
    assert spec.status == "draft"
    assert spec.category == "ring"
    assert spec.estimated_rough_metal_weight_grams == 6.5
    assert spec.estimated_finished_metal_weight_grams == 5.8
    assert spec.total_gemstone_count == 1
    assert spec.estimated_total_bench_hours == 4.5
    assert spec.complexity_rating == "moderate"
    assert spec.ai_confidence_score == 0.92
    assert spec.created_at is not None
    assert spec.updated_at is not None


def test_production_material_creation(db_session: Session):
    """Test 2: Verify ProductionMaterial line item creation."""
    user = create_user(db_session, "mat.create@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
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
        plating="none",
        estimated_weight_grams=5.8,
        casting_loss_percentage=10.0,
    )
    db_session.add(mat)
    db_session.commit()
    db_session.refresh(mat)

    assert mat.id is not None
    assert mat.metal_type == "gold"
    assert mat.metal_purity == "18k"
    assert mat.metal_color == "yellow"
    assert mat.metal_finish == "high_polish"
    assert mat.estimated_weight_grams == 5.8
    assert mat.casting_loss_percentage == 10.0


def test_production_gemstone_creation(db_session: Session):
    """Test 3: Verify ProductionGemstone line item creation."""
    user = create_user(db_session, "gem.create@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
    )
    db_session.add(spec)
    db_session.commit()

    gem = ProductionGemstone(
        id=uuid.uuid4(),
        specification_id=spec.id,
        gemstone_type="emerald",
        cut_shape="cushion",
        stone_count=1,
        estimated_carat_weight=1.5,
        approximate_dimensions_mm="7.0x5.5mm",
        setting_type="bezel",
        is_center_stone=True,
    )
    db_session.add(gem)
    db_session.commit()
    db_session.refresh(gem)

    assert gem.id is not None
    assert gem.gemstone_type == "emerald"
    assert gem.cut_shape == "cushion"
    assert gem.stone_count == 1
    assert gem.estimated_carat_weight == 1.5
    assert gem.approximate_dimensions_mm == "7.0x5.5mm"
    assert gem.setting_type == "bezel"
    assert gem.is_center_stone is True


def test_production_step_creation(db_session: Session):
    """Test 4: Verify ProductionStep creation with stage parameters."""
    user = create_user(db_session, "step.create@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
    )
    db_session.add(spec)
    db_session.commit()

    step = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=1,
        stage_name="Investment Casting",
        required_skill="casting",
        required_machine_type="casting_furnace",
        base_hours=2.0,
        per_unit_hours=0.5,
        description="Vacuum investment casting with 18k yellow gold grain.",
        quality_checkpoint="Zero porosity on shank surface.",
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)

    assert step.id is not None
    assert step.step_number == 1
    assert step.stage_name == "Investment Casting"
    assert step.required_skill == "casting"
    assert step.required_machine_type == "casting_furnace"
    assert step.base_hours == 2.0
    assert step.per_unit_hours == 0.5
    assert step.quality_checkpoint == "Zero porosity on shank surface."


# ==============================================================================
# Relationships & Lineage Tests
# ==============================================================================

def test_specification_full_relationships(db_session: Session):
    """Test 5: Verify bidirectional relationships between User, Design, Render, Spec, and child items."""
    user = create_user(db_session, "spec.rel@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)

    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        category="ring",
    )
    db_session.add(spec)

    mat1 = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type="platinum",
        metal_purity="950",
    )
    gem1 = ProductionGemstone(
        id=uuid.uuid4(),
        specification_id=spec.id,
        gemstone_type="diamond",
        stone_count=12,
    )
    step1 = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=1,
        stage_name="Stone Setting",
        required_skill="stone_setting",
        base_hours=1.5,
        per_unit_hours=0.25,
    )
    db_session.add_all([mat1, gem1, step1])
    db_session.commit()

    db_session.refresh(spec)
    db_session.refresh(design)
    db_session.refresh(render)
    db_session.refresh(user)

    # Forward navigation from specification
    assert spec.user.id == user.id
    assert spec.design.id == design.id
    assert spec.render.id == render.id
    assert len(spec.materials) == 1
    assert spec.materials[0].metal_type == "platinum"
    assert len(spec.gemstones) == 1
    assert spec.gemstones[0].gemstone_type == "diamond"
    assert len(spec.steps) == 1
    assert spec.steps[0].stage_name == "Stone Setting"

    # Reverse navigation from parent entities
    assert len(design.specifications) == 1
    assert design.specifications[0].id == spec.id
    assert len(render.specifications) == 1
    assert render.specifications[0].id == spec.id
    assert len(user.specifications) == 1
    assert user.specifications[0].id == spec.id


def test_multiple_specifications_per_design(db_session: Session):
    """Test 6: Verify a design supports multiple specification versions (e.g. V1, V2)."""
    user = create_user(db_session, "multi.spec@jewelmind.com")
    design = create_design(db_session, user)
    render_v1 = create_render(db_session, design, user, version=1, image_url="https://url/v1.png")
    render_v2 = create_render(db_session, design, user, version=2, image_url="https://url/v2.png")

    spec_v1 = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render_v1.id,
        version_number=1,
        status="archived",
        category="ring",
    )
    spec_v2 = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render_v2.id,
        version_number=2,
        status="approved",
        category="ring",
    )
    db_session.add_all([spec_v1, spec_v2])
    db_session.commit()

    db_session.refresh(design)
    assert len(design.specifications) == 2
    assert design.specifications[0].version_number == 1
    assert design.specifications[1].version_number == 2


def test_specification_version_uniqueness(db_session: Session):
    """Test 7: Verify unique constraint on (user_id, design_id, version_number)."""
    user = create_user(db_session, "uniq.spec@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)

    spec1 = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
    )
    db_session.add(spec1)
    db_session.commit()

    # Attempt duplicate version for same user and design
    spec2 = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
    )
    db_session.add(spec2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ==============================================================================
# Check Constraint Validation Tests
# ==============================================================================

def test_gemstone_count_validation(db_session: Session):
    """Test 8: Verify negative stone count is rejected by check constraint."""
    user = create_user(db_session, "ck.gem@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
    )
    db_session.add(spec)
    db_session.commit()

    gem = ProductionGemstone(
        id=uuid.uuid4(),
        specification_id=spec.id,
        gemstone_type="diamond",
        stone_count=-5,  # Invalid
    )
    db_session.add(gem)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_step_validation(db_session: Session):
    """Test 9: Verify step_number > 0 and base_hours >= 0 constraints."""
    user = create_user(db_session, "ck.step@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
    )
    db_session.add(spec)
    db_session.commit()

    # Invalid step number: 0
    step_invalid_num = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=0,
        stage_name="Casting",
        required_skill="casting",
        base_hours=1.0,
        per_unit_hours=0.5,
    )
    db_session.add(step_invalid_num)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Invalid negative hours
    step_invalid_hours = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=1,
        stage_name="Casting",
        required_skill="casting",
        base_hours=-2.0,
        per_unit_hours=0.5,
    )
    db_session.add(step_invalid_hours)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_ai_confidence_validation(db_session: Session):
    """Test 10: Verify ai_confidence_score range (0.0 to 1.0) constraint."""
    user = create_user(db_session, "ck.conf@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)

    # Score > 1.0 is invalid
    spec_invalid = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
        ai_confidence_score=1.5,
    )
    db_session.add(spec_invalid)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Score < 0.0 is invalid
    spec_invalid_neg = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
        ai_confidence_score=-0.1,
    )
    db_session.add(spec_invalid_neg)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_specification_status_and_complexity_constraints(db_session: Session):
    """Verify status must be draft/approved/archived and complexity valid."""
    user = create_user(db_session, "ck.status@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)

    # Invalid status
    spec_bad_status = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="invalid_status",
        category="ring",
    )
    db_session.add(spec_bad_status)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Invalid complexity
    spec_bad_comp = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
        complexity_rating="impossible_level",
    )
    db_session.add(spec_bad_comp)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ==============================================================================
# ProductionOrder Linkage & Backward Compatibility Tests
# ==============================================================================

def test_production_order_nullable_specification(db_session: Session):
    """Test 11: Verify production orders can exist without a specification_id (backward compatibility)."""
    user = create_user(db_session, "order.null_spec@jewelmind.com")
    design = create_design(db_session, user)

    order = ProductionOrder(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        quantity=5,
        priority="high",
        status="pending",
        deadline=datetime.now(timezone.utc),
        specification_id=None,  # Nullable
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    assert order.id is not None
    assert order.specification_id is None
    assert order.specification is None


def test_production_order_references_specification(db_session: Session):
    """Test 12: Verify production order links to specification and loads relationship."""
    user = create_user(db_session, "order.with_spec@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        category="ring",
    )
    db_session.add(spec)
    db_session.commit()

    order = ProductionOrder(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        specification_id=spec.id,
        quantity=1,
        priority="urgent",
        status="pending",
        deadline=datetime.now(timezone.utc),
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    assert order.specification_id == spec.id
    assert order.specification.id == spec.id
    assert len(spec.production_orders) == 1
    assert spec.production_orders[0].id == order.id


def test_specification_to_render_relationship(db_session: Session):
    """Test 13: Verify specification.render points to the exact DesignRender."""
    user = create_user(db_session, "spec.render_exact@jewelmind.com")
    design = create_design(db_session, user)
    render_v3 = create_render(db_session, design, user, version=3, image_url="https://url/v3.png")

    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render_v3.id,
        version_number=1,
        status="approved",
        category="ring",
    )
    db_session.add(spec)
    db_session.commit()
    db_session.refresh(spec)

    assert spec.render.id == render_v3.id
    assert spec.render.version_number == 3
    assert spec.render.image_url == "https://url/v3.png"


def test_render_deletion_protection_by_specification(db_session: Session):
    """Test 14: Deleting a DesignRender referenced by a ProductionSpecification is blocked (ON DELETE RESTRICT)."""
    user = create_user(db_session, "render.restrict@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user, version=1)

    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        category="ring",
    )
    db_session.add(spec)
    db_session.commit()

    # Attempt to delete the referenced render
    db_session.delete(render)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ==============================================================================
# Cascade Cleanup of Child BOM Entities Tests
# ==============================================================================

def test_cascade_deletion_materials(db_session: Session):
    """Test 15: Deleting a specification cascades to delete its materials."""
    user = create_user(db_session, "casc.mat@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
    )
    db_session.add(spec)
    mat = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type="gold",
        metal_purity="14k",
    )
    db_session.add(mat)
    db_session.commit()

    mat_id = mat.id
    db_session.delete(spec)
    db_session.commit()

    assert db_session.query(ProductionMaterial).filter(ProductionMaterial.id == mat_id).first() is None


def test_cascade_deletion_gemstones(db_session: Session):
    """Test 16: Deleting a specification cascades to delete its gemstones."""
    user = create_user(db_session, "casc.gem@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
    )
    db_session.add(spec)
    gem = ProductionGemstone(
        id=uuid.uuid4(),
        specification_id=spec.id,
        gemstone_type="sapphire",
        stone_count=3,
    )
    db_session.add(gem)
    db_session.commit()

    gem_id = gem.id
    db_session.delete(spec)
    db_session.commit()

    assert db_session.query(ProductionGemstone).filter(ProductionGemstone.id == gem_id).first() is None


def test_cascade_deletion_steps(db_session: Session):
    """Test 17: Deleting a specification cascades to delete its steps."""
    user = create_user(db_session, "casc.step@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
    )
    db_session.add(spec)
    step = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=1,
        stage_name="Polishing",
        required_skill="polishing",
        base_hours=1.0,
        per_unit_hours=0.5,
    )
    db_session.add(step)
    db_session.commit()

    step_id = step.id
    db_session.delete(spec)
    db_session.commit()

    assert db_session.query(ProductionStep).filter(ProductionStep.id == step_id).first() is None


# ==============================================================================
# Service Operations & ProductionOrder Backward Compatibility Tests
# ==============================================================================

def test_existing_production_service_compatibility(db_session: Session):
    """Test 18: Verify ProductionService create_order and update_order support specification_id seamlessly."""
    user = create_user(db_session, "svc.compat@jewelmind.com")
    design = create_design(db_session, user)
    render = create_render(db_session, design, user)

    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        category="ring",
    )
    db_session.add(spec)
    db_session.commit()

    # 1. Create order without specification (legacy behavior)
    legacy_in = ProductionOrderCreate(
        design_id=design.id,
        quantity=2,
        priority=OrderPriority.MEDIUM,
        status=OrderStatus.PENDING,
        deadline=datetime.now(timezone.utc),
    )
    order_res1 = production_service.create_order(db_session, user.id, legacy_in)
    assert order_res1.specification_id is None

    # 2. Update order with specification_id
    update_in = ProductionOrderUpdate(specification_id=spec.id)
    order_res2 = production_service.update_order(db_session, user.id, order_res1.id, update_in)
    assert order_res2.specification_id == spec.id

    # 3. Create order directly with specification_id
    new_in = ProductionOrderCreate(
        design_id=design.id,
        quantity=1,
        priority=OrderPriority.URGENT,
        status=OrderStatus.PENDING,
        deadline=datetime.now(timezone.utc),
        render_id=render.id,
        specification_id=spec.id,
    )
    order_res3 = production_service.create_order(db_session, user.id, new_in)
    assert order_res3.specification_id == spec.id
    assert order_res3.render_id == render.id
