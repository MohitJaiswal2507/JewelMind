"""
Phase I.5 — Production Order Integration & CP-SAT Scheduling Test Suite
Verifies:
A. Approved specification -> production order succeeds
B. Draft specification -> rejected
C. Archived specification -> rejected
D. Cross-user specification -> rejected (IDOR prevention 404)
E. Specification/render mismatch -> rejected
F. Exact specification_id stored on order
G. Exact render_id stored on order
H. Approved render URL preserved
I. Specification materials become order BOM / accessible manufacturing data
J. Specification gemstone requirements preserved
K. Specification routing becomes operations
L. Dynamic operation count works
M. 3-step routing works
N. 5+ step routing works
O. Gem-free routing does not invent stone-setting
P. Operation sequence preserved
Q. Duration calculation valid
R. Negative duration rejected
S. Worker skill constraints respected
T. Machine constraints respected
U. CP-SAT receives real specification-derived operations
V. Precedence constraints respected
W. Infeasible schedule handled correctly
X. Failed operation creation rolls back order atomically
Y. Approved specification cannot be modified through order workflow
Z. Cross-user render/specification access blocked
"""

import math
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token
from app.models.design import Design, DesignRender
from app.models.production import Machine, ProductionOrder, Worker
from app.models.specification import (
    ProductionGemstone,
    ProductionMaterial,
    ProductionSpecification,
    ProductionStep,
)
from app.models.user import User
from app.schemas.auth import UserCreate
from app.schemas.optimization import OptimizationRequest, SolverStatusEnum
from app.schemas.production import (
    OrderPriority,
    OrderStatus,
    ProductionOrderCreateFromSpecification,
)
from app.services.production_optimization_service import production_optimization_service
from app.services.production_service import production_service
from app.services.user_service import user_service


# ---------------------------------------------------------------------------
# Test Helpers & Fixtures
# ---------------------------------------------------------------------------

def create_test_user(db_session: Session, email: str = "artisan.i5@jewelmind.com") -> User:
    """Creates a distinct user for testing."""
    return user_service.create(
        db_session,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Artisan Tester",
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
    status: str = "approved",
    include_gemstones: bool = True,
    step_count: int = 3,
    custom_steps: list = None,
    render_approved: bool = True,
) -> tuple[ProductionSpecification, Design, DesignRender]:
    """Creates a complete design, render, specification tree with BOM and routing steps."""
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Artisan Masterpiece Ring",
        category="ring",
        status="ready",
        ai_prompt="18k gold sapphire engagement ring",
        rendered_image_url="https://storage.jewelmind.internal/renders/ring_master.png",
    )
    db_session.add(design)
    db_session.commit()

    render = DesignRender(
        id=uuid.uuid4(),
        design_id=design.id,
        user_id=user.id,
        version_number=1,
        render_mode="text",
        prompt="18k gold sapphire ring",
        enhanced_prompt="An 18k yellow gold sapphire solitaire ring with diamond accents",
        image_url="https://storage.jewelmind.internal/renders/ring_master.png",
        thumbnail_url="https://storage.jewelmind.internal/renders/ring_master.png",
        seed=101,
        is_approved_for_production=render_approved,
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
        estimated_rough_metal_weight_grams=6.2,
        estimated_finished_metal_weight_grams=5.4,
        total_gemstone_count=3 if include_gemstones else 0,
        estimated_total_bench_hours=12.0,
        complexity_rating="intricate",
        fabrication_notes="Precision hand-forged shank with micro-pavé setting.",
        ai_confidence_score=0.92,
        approved_at=datetime.now(timezone.utc) if status == "approved" else None,
    )
    db_session.add(spec)
    db_session.commit()

    # Materials
    mat = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type="gold",
        metal_purity="18k",
        metal_color="yellow",
        metal_finish="mirror_polish",
        estimated_weight_grams=5.4,
        casting_loss_percentage=10.0,
    )
    db_session.add(mat)

    # Gemstones
    if include_gemstones:
        gem = ProductionGemstone(
            id=uuid.uuid4(),
            specification_id=spec.id,
            gemstone_type="sapphire",
            cut_shape="oval",
            stone_count=1,
            estimated_carat_weight=1.5,
            setting_type="prong",
            is_center_stone=True,
        )
        db_session.add(gem)

    # Routing Steps
    if custom_steps:
        for s_data in custom_steps:
            step = ProductionStep(
                id=uuid.uuid4(),
                specification_id=spec.id,
                step_number=s_data["step_number"],
                stage_name=s_data["stage_name"],
                required_skill=s_data["required_skill"],
                required_machine_type=s_data.get("required_machine_type"),
                base_hours=s_data["base_hours"],
                per_unit_hours=s_data["per_unit_hours"],
                description=s_data.get("description", "Step instruction"),
                quality_checkpoint=s_data.get("quality_checkpoint"),
            )
            db_session.add(step)
    else:
        # Default steps based on step_count
        step_definitions = [
            {"step_number": 1, "stage_name": "CAD & Wax 3D Printing", "required_skill": "cad_design", "required_machine_type": "3d_wax_printer", "base_hours": 1.5, "per_unit_hours": 0.5, "quality_checkpoint": "Check wax tolerances"},
            {"step_number": 2, "stage_name": "Investment Casting", "required_skill": "casting", "required_machine_type": "casting_furnace", "base_hours": 2.0, "per_unit_hours": 0.5, "quality_checkpoint": "Check for porosity"},
            {"step_number": 3, "stage_name": "Stone Setting", "required_skill": "stone_setting", "required_machine_type": None, "base_hours": 2.5, "per_unit_hours": 1.0, "quality_checkpoint": "Verify prong tension"},
            {"step_number": 4, "stage_name": "Hand Polishing", "required_skill": "polishing", "required_machine_type": "polishing_lathe", "base_hours": 1.0, "per_unit_hours": 0.5, "quality_checkpoint": "Inspect mirror finish"},
            {"step_number": 5, "stage_name": "Quality Assurance & Hallmarking", "required_skill": "engraving", "required_machine_type": "laser_engraver", "base_hours": 0.5, "per_unit_hours": 0.2, "quality_checkpoint": "Final purity stamp verify"},
        ]
        for s_data in step_definitions[:step_count]:
            step = ProductionStep(
                id=uuid.uuid4(),
                specification_id=spec.id,
                step_number=s_data["step_number"],
                stage_name=s_data["stage_name"],
                required_skill=s_data["required_skill"],
                required_machine_type=s_data["required_machine_type"],
                base_hours=s_data["base_hours"],
                per_unit_hours=s_data["per_unit_hours"],
                description=f"Standard execution for {s_data['stage_name']}",
                quality_checkpoint=s_data["quality_checkpoint"],
            )
            db_session.add(step)

    db_session.commit()
    db_session.refresh(spec)
    return spec, design, render


def setup_standard_workshop(db_session: Session, user: User) -> tuple[list[Worker], list[Machine]]:
    """Creates a well-equipped jewellery workshop with skilled artisans and machines."""
    workers = [
        Worker(user_id=user.id, name="Aarav CAD Master", skill="cad_design", capacity_hours_per_day=8.0, is_available=True),
        Worker(user_id=user.id, name="Bhavna Goldsmith", skill="casting", capacity_hours_per_day=8.0, is_available=True),
        Worker(user_id=user.id, name="Chetan Setter", skill="stone_setting", capacity_hours_per_day=8.0, is_available=True),
        Worker(user_id=user.id, name="Devi Polisher", skill="polishing", capacity_hours_per_day=8.0, is_available=True),
        Worker(user_id=user.id, name="Eshwar Engraver", skill="engraving", capacity_hours_per_day=8.0, is_available=True),
    ]
    for w in workers:
        db_session.add(w)

    machines = [
        Machine(user_id=user.id, name="Wax Pro 3D", machine_type="3d_wax_printer", capacity_hours_per_day=12.0, is_available=True),
        Machine(user_id=user.id, name="Induction Furnace 500", machine_type="casting_furnace", capacity_hours_per_day=10.0, is_available=True),
        Machine(user_id=user.id, name="Speed Lathe 2000", machine_type="polishing_lathe", capacity_hours_per_day=10.0, is_available=True),
        Machine(user_id=user.id, name="Fiber Laser Engraver", machine_type="laser_engraver", capacity_hours_per_day=8.0, is_available=True),
    ]
    for m in machines:
        db_session.add(m)

    db_session.commit()
    return workers, machines


# ---------------------------------------------------------------------------
# Tests A - H: Order Creation from Specification & Lineage Integrity
# ---------------------------------------------------------------------------

def test_a_approved_specification_to_order_succeeds(client: TestClient, db_session: Session):
    """Test A: Approved specification creates production order successfully via API."""
    user = create_test_user(db_session, "user.a@jewelmind.com")
    headers = get_auth_headers(user)
    spec, design, render = create_specification_tree(db_session, user, status="approved")

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {
        "specification_id": str(spec.id),
        "quantity": 2,
        "priority": "high",
        "deadline": deadline,
        "notes": "Urgent custom order for VIP client.",
    }

    res = client.post("/api/v1/production/orders/from-specification", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["specification_id"] == str(spec.id)
    assert data["design_id"] == str(design.id)
    assert data["render_id"] == str(render.id)
    assert data["approved_render_url"] == render.image_url
    assert data["quantity"] == 2
    assert data["priority"] == "high"
    assert data["status"] == "pending"
    assert data["specification_version"] == 1
    assert data["specification_category"] == "ring"
    assert data["routing_steps_count"] == 3
    assert data["materials_count"] == 1
    assert data["gemstones_count"] == 1


def test_b_draft_specification_rejected(client: TestClient, db_session: Session):
    """Test B: Draft specification is strictly rejected with 400 Bad Request."""
    user = create_test_user(db_session, "user.b@jewelmind.com")
    headers = get_auth_headers(user)
    spec, _, _ = create_specification_tree(db_session, user, status="draft")

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {
        "specification_id": str(spec.id),
        "quantity": 1,
        "deadline": deadline,
    }

    res = client.post("/api/v1/production/orders/from-specification", json=payload, headers=headers)
    assert res.status_code == 400
    msg = res.json().get("error", {}).get("message", "").lower()
    assert "draft" in msg or "approved" in msg


def test_c_archived_specification_rejected(client: TestClient, db_session: Session):
    """Test C: Archived specification is rejected with 400 Bad Request."""
    user = create_test_user(db_session, "user.c@jewelmind.com")
    headers = get_auth_headers(user)
    spec, _, _ = create_specification_tree(db_session, user, status="archived")

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {
        "specification_id": str(spec.id),
        "quantity": 1,
        "deadline": deadline,
    }

    res = client.post("/api/v1/production/orders/from-specification", json=payload, headers=headers)
    assert res.status_code == 400
    msg = res.json().get("error", {}).get("message", "").lower()
    assert "archived" in msg or "approved" in msg


def test_d_cross_user_specification_rejected(client: TestClient, db_session: Session):
    """Test D: Another user's specification lookup returns 404 (IDOR safe)."""
    user_owner = create_test_user(db_session, "owner.d@jewelmind.com")
    user_attacker = create_test_user(db_session, "attacker.d@jewelmind.com")
    headers_attacker = get_auth_headers(user_attacker)

    spec, _, _ = create_specification_tree(db_session, user_owner, status="approved")

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {
        "specification_id": str(spec.id),
        "quantity": 1,
        "deadline": deadline,
    }

    res = client.post("/api/v1/production/orders/from-specification", json=payload, headers=headers_attacker)
    assert res.status_code == 404
    msg = res.json().get("error", {}).get("message", "").lower()
    assert "not found" in msg


def test_e_specification_render_mismatch_rejected(client: TestClient, db_session: Session):
    """Test E: Specification whose render is not approved for production is rejected."""
    user = create_test_user(db_session, "user.e@jewelmind.com")
    headers = get_auth_headers(user)
    spec, _, _ = create_specification_tree(db_session, user, status="approved", render_approved=False)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {
        "specification_id": str(spec.id),
        "quantity": 1,
        "deadline": deadline,
    }

    res = client.post("/api/v1/production/orders/from-specification", json=payload, headers=headers)
    assert res.status_code == 400
    msg = res.json().get("error", {}).get("message", "").lower()
    assert "render" in msg or "approved" in msg


def test_f_g_h_exact_ids_and_render_url_stored(db_session: Session):
    """Test F, G, H: Exact specification_id, render_id, and approved_render_url stored."""
    user = create_test_user(db_session, "user.fgh@jewelmind.com")
    spec, design, render = create_specification_tree(db_session, user, status="approved")

    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=3,
        priority=OrderPriority.HIGH,
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
        notes="Testing lineage storage",
    )

    order_res = production_service.create_order_from_specification(db_session, user.id, req)

    # Check exact IDs stored
    assert order_res.specification_id == spec.id
    assert order_res.render_id == spec.render_id == render.id
    assert order_res.design_id == design.id
    assert order_res.approved_render_url == render.image_url

    # Check in DB
    order_db = db_session.query(ProductionOrder).filter(ProductionOrder.id == order_res.id).first()
    assert order_db is not None
    assert order_db.specification_id == spec.id
    assert order_db.render_id == render.id
    assert order_db.approved_render_url == render.image_url


# ---------------------------------------------------------------------------
# Tests I - P: BOM & Routing Integration
# ---------------------------------------------------------------------------

def test_i_j_specification_materials_and_gemstones_accessible(db_session: Session):
    """Test I & J: Materials BOM and gemstone requirements remain accessible through order."""
    user = create_test_user(db_session, "user.ij@jewelmind.com")
    spec, _, _ = create_specification_tree(db_session, user, status="approved", include_gemstones=True)

    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
    )
    order_res = production_service.create_order_from_specification(db_session, user.id, req)

    # Retrieve order with relationship
    order_db = db_session.query(ProductionOrder).filter(ProductionOrder.id == order_res.id).first()
    assert order_db.specification is not None
    assert len(order_db.specification.materials) == 1
    mat = order_db.specification.materials[0]
    assert mat.metal_type == "gold"
    assert mat.metal_purity == "18k"
    assert mat.metal_finish == "mirror_polish"
    assert mat.estimated_weight_grams == 5.4

    assert len(order_db.specification.gemstones) == 1
    gem = order_db.specification.gemstones[0]
    assert gem.gemstone_type == "sapphire"
    assert gem.estimated_carat_weight == 1.5
    assert gem.cut_shape == "oval"
    assert gem.is_center_stone is True


def test_k_l_m_n_dynamic_routing_counts(db_session: Session):
    """Test K, L, M, N: Dynamic operations count works for 3-step, 5-step routing in CP-SAT."""
    user = create_test_user(db_session, "user.dynamic@jewelmind.com")
    setup_standard_workshop(db_session, user)

    # 1. Test 3-step routing
    spec_3, _, _ = create_specification_tree(db_session, user, status="approved", step_count=3)
    req_3 = ProductionOrderCreateFromSpecification(
        specification_id=spec_3.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=10),
    )
    order_3 = production_service.create_order_from_specification(db_session, user.id, req_3)

    opt_req_3 = OptimizationRequest(order_ids=[order_3.id], horizon_days=10, persist_schedule=False)
    opt_res_3 = production_optimization_service.optimize(db_session, user.id, opt_req_3)
    assert opt_res_3.status in ("success", "feasible")
    assert len(opt_res_3.schedule) == 3, f"Expected 3 tasks, got {len(opt_res_3.schedule)}"
    assert [t.sequence_order for t in opt_res_3.schedule] == [1, 2, 3]

    # 2. Test 5-step routing
    spec_5, _, _ = create_specification_tree(db_session, user, status="approved", step_count=5)
    req_5 = ProductionOrderCreateFromSpecification(
        specification_id=spec_5.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=10),
    )
    order_5 = production_service.create_order_from_specification(db_session, user.id, req_5)

    opt_req_5 = OptimizationRequest(order_ids=[order_5.id], horizon_days=10, persist_schedule=False)
    opt_res_5 = production_optimization_service.optimize(db_session, user.id, opt_req_5)
    assert opt_res_5.status in ("success", "feasible")
    assert len(opt_res_5.schedule) == 5, f"Expected 5 tasks, got {len(opt_res_5.schedule)}"
    assert [t.sequence_order for t in opt_res_5.schedule] == [1, 2, 3, 4, 5]


def test_o_gem_free_routing_does_not_invent_stone_setting(db_session: Session):
    """Test O: Gem-free routing (plain gold wedding band) does not invent stone setting."""
    user = create_test_user(db_session, "user.gemfree@jewelmind.com")
    setup_standard_workshop(db_session, user)

    plain_band_steps = [
        {"step_number": 1, "stage_name": "Investment Casting", "required_skill": "casting", "required_machine_type": "casting_furnace", "base_hours": 2.0, "per_unit_hours": 0.5},
        {"step_number": 2, "stage_name": "Lathe Polishing", "required_skill": "polishing", "required_machine_type": "polishing_lathe", "base_hours": 1.5, "per_unit_hours": 0.5},
        {"step_number": 3, "stage_name": "Laser Hallmark", "required_skill": "engraving", "required_machine_type": "laser_engraver", "base_hours": 0.5, "per_unit_hours": 0.2},
    ]

    spec, _, _ = create_specification_tree(
        db_session,
        user,
        status="approved",
        include_gemstones=False,
        custom_steps=plain_band_steps,
    )
    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
    )
    order = production_service.create_order_from_specification(db_session, user.id, req)

    opt_req = OptimizationRequest(order_ids=[order.id], horizon_days=7, persist_schedule=False)
    opt_res = production_optimization_service.optimize(db_session, user.id, opt_req)

    assert opt_res.status in ("success", "feasible")
    op_names = [t.operation_name.lower() for t in opt_res.schedule]
    assert not any("stone" in name or "setting" in name for name in op_names), (
        f"Plain band operations should not have stone setting: {op_names}"
    )


def test_p_operation_sequence_preserved(db_session: Session):
    """Test P: Operation sequence 1 -> 2 -> 3 is strictly preserved in scheduled tasks."""
    user = create_test_user(db_session, "user.seq@jewelmind.com")
    setup_standard_workshop(db_session, user)

    spec, _, _ = create_specification_tree(db_session, user, status="approved", step_count=4)
    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
    )
    order = production_service.create_order_from_specification(db_session, user.id, req)

    opt_req = OptimizationRequest(order_ids=[order.id], horizon_days=7, persist_schedule=False)
    opt_res = production_optimization_service.optimize(db_session, user.id, opt_req)

    assert opt_res.status in ("success", "feasible")
    order_tasks = sorted([t for t in opt_res.schedule if t.order_id == order.id], key=lambda t: t.sequence_order)
    for i, t in enumerate(order_tasks, start=1):
        assert t.sequence_order == i
        assert t.step_number == i


# ---------------------------------------------------------------------------
# Tests Q - R: Duration Calculations and Constraints
# ---------------------------------------------------------------------------

def test_q_duration_calculation_valid(db_session: Session):
    """Test Q: Duration correctly calculated as math.ceil(base_hours + per_unit_hours * quantity)."""
    user = create_test_user(db_session, "user.dur@jewelmind.com")
    setup_standard_workshop(db_session, user)

    custom_steps = [
        {"step_number": 1, "stage_name": "Casting", "required_skill": "casting", "required_machine_type": "casting_furnace", "base_hours": 2.0, "per_unit_hours": 0.5},
        {"step_number": 2, "stage_name": "Polishing", "required_skill": "polishing", "required_machine_type": "polishing_lathe", "base_hours": 1.0, "per_unit_hours": 0.75},
    ]
    spec, _, _ = create_specification_tree(db_session, user, status="approved", custom_steps=custom_steps)

    # Quantity = 4
    # Step 1: 2.0 + (0.5 * 4) = 4.0 hours
    # Step 2: 1.0 + (0.75 * 4) = 4.0 hours
    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=4,
        deadline=datetime.now(timezone.utc) + timedelta(days=10),
    )
    order = production_service.create_order_from_specification(db_session, user.id, req)

    opt_req = OptimizationRequest(order_ids=[order.id], horizon_days=10, persist_schedule=False)
    opt_res = production_optimization_service.optimize(db_session, user.id, opt_req)

    assert opt_res.status in ("success", "feasible")
    for task in opt_res.schedule:
        assert task.duration_hours == 4.0


def test_r_negative_duration_rejected(db_session: Session):
    """Test R: Specification with negative duration steps is rejected when attempting to create an order."""
    from unittest.mock import patch
    user = create_test_user(db_session, "user.negdur@jewelmind.com")

    spec, design, render = create_specification_tree(db_session, user, status="approved", step_count=1)

    # 1. Verify database-level check constraint rejects negative base_hours
    with pytest.raises(Exception):
        spec.steps[0].base_hours = -2.0
        db_session.commit()
    db_session.rollback()

    # 2. Verify service-level validation rejects negative step duration
    spec, design, render = create_specification_tree(db_session, user, status="approved", step_count=1)
    spec.steps[0].base_hours = -1.5

    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
    )

    with patch.object(db_session, "scalar", side_effect=[spec, design, render]):
        with pytest.raises(AppException) as exc_info:
            production_service.create_order_from_specification(db_session, user.id, req)

        assert exc_info.value.status_code == 400
        assert "negative" in str(exc_info.value.message).lower()


# ---------------------------------------------------------------------------
# Tests S - W: Worker, Machine, Precedence & Feasibility in CP-SAT
# ---------------------------------------------------------------------------

def test_s_t_worker_skill_and_machine_compatibility_enforced(db_session: Session):
    """Test S & T: Assigned artisan matches required skill and assigned machine matches required machine."""
    user = create_test_user(db_session, "user.skills@jewelmind.com")
    workers, machines = setup_standard_workshop(db_session, user)

    worker_map = {w.id: w for w in workers}
    machine_map = {m.id: m for m in machines}

    spec, _, _ = create_specification_tree(db_session, user, status="approved", step_count=4)
    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=10),
    )
    order = production_service.create_order_from_specification(db_session, user.id, req)

    opt_req = OptimizationRequest(order_ids=[order.id], horizon_days=10, persist_schedule=False)
    opt_res = production_optimization_service.optimize(db_session, user.id, opt_req)

    assert opt_res.status in ("success", "feasible")
    for task in opt_res.schedule:
        assigned_w = worker_map[task.worker_id]
        if task.operation_name == "CAD & Wax 3D Printing":
            assert assigned_w.skill in ("cad_design", "general")
            assert task.machine_id is not None
            assert machine_map[task.machine_id].machine_type in ("3d_wax_printer", "general")
        elif task.operation_name == "Investment Casting":
            assert assigned_w.skill in ("casting", "general")
            assert task.machine_id is not None
            assert machine_map[task.machine_id].machine_type in ("casting_furnace", "general")
        elif task.operation_name == "Stone Setting":
            assert assigned_w.skill in ("stone_setting", "general")
        elif task.operation_name == "Hand Polishing":
            assert assigned_w.skill in ("polishing", "general")
            assert task.machine_id is not None
            assert machine_map[task.machine_id].machine_type in ("polishing_lathe", "general")


def test_v_precedence_constraints_respected(db_session: Session):
    """Test V: For sequential operations, start(op N) >= end(op N-1)."""
    user = create_test_user(db_session, "user.prec@jewelmind.com")
    setup_standard_workshop(db_session, user)

    spec, _, _ = create_specification_tree(db_session, user, status="approved", step_count=5)
    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=2,
        deadline=datetime.now(timezone.utc) + timedelta(days=14),
    )
    order = production_service.create_order_from_specification(db_session, user.id, req)

    opt_req = OptimizationRequest(order_ids=[order.id], horizon_days=14, persist_schedule=False)
    opt_res = production_optimization_service.optimize(db_session, user.id, opt_req)

    assert opt_res.status in ("success", "feasible")
    tasks = sorted(opt_res.schedule, key=lambda t: t.sequence_order)
    for i in range(len(tasks) - 1):
        prev_task = tasks[i]
        curr_task = tasks[i + 1]
        assert curr_task.start_time >= prev_task.end_time, (
            f"Precedence violation: {curr_task.operation_name} started at {curr_task.start_time} "
            f"before {prev_task.operation_name} ended at {prev_task.end_time}"
        )


def test_w_infeasible_schedule_handled_correctly(db_session: Session):
    """Test W: When required skill is missing among available workers, solver returns INFEASIBLE with diagnosis."""
    user = create_test_user(db_session, "user.infeasible@jewelmind.com")

    # Workshop has only a polisher
    w = Worker(user_id=user.id, name="Sole Polisher", skill="polishing", capacity_hours_per_day=8.0, is_available=True)
    db_session.add(w)
    db_session.commit()

    # Step requires casting
    custom_steps = [
        {"step_number": 1, "stage_name": "Investment Casting", "required_skill": "casting", "required_machine_type": None, "base_hours": 2.0, "per_unit_hours": 0.5},
    ]
    spec, _, _ = create_specification_tree(db_session, user, status="approved", custom_steps=custom_steps)

    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
    )
    order = production_service.create_order_from_specification(db_session, user.id, req)

    opt_req = OptimizationRequest(order_ids=[order.id], horizon_days=5, persist_schedule=False)
    opt_res = production_optimization_service.optimize(db_session, user.id, opt_req)

    assert opt_res.status == "infeasible"
    assert opt_res.solver_status == SolverStatusEnum.INFEASIBLE
    assert len(opt_res.infeasibility_reasons) > 0
    assert any("casting" in r.lower() or "artisan" in r.lower() for r in opt_res.infeasibility_reasons)


# ---------------------------------------------------------------------------
# Tests X - Z: Atomicity, Immutability & Multi-Tenant Security
# ---------------------------------------------------------------------------

def test_x_atomic_rollback_on_failure(db_session: Session):
    """Test X: If order creation validation fails, transaction rolls back and leaves no orphaned records."""
    user = create_test_user(db_session, "user.rollback@jewelmind.com")
    spec, _, _ = create_specification_tree(db_session, user, status="approved")

    # Non-sequential step numbers to force failure
    step_bad = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=99,  # Non-sequential!
        stage_name="Disjoint Step",
        required_skill="polishing",
        base_hours=1.0,
        per_unit_hours=0.5,
    )
    db_session.add(step_bad)
    db_session.commit()

    initial_orders_count = db_session.query(ProductionOrder).filter(ProductionOrder.user_id == user.id).count()

    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
    )

    with pytest.raises(AppException) as exc_info:
        production_service.create_order_from_specification(db_session, user.id, req)

    assert exc_info.value.status_code == 400
    assert "non-sequential" in str(exc_info.value.message).lower() or "sequential" in str(exc_info.value.message).lower()

    # Verify zero orders were created
    final_orders_count = db_session.query(ProductionOrder).filter(ProductionOrder.user_id == user.id).count()
    assert final_orders_count == initial_orders_count


def test_y_approved_specification_remains_immutable(client: TestClient, db_session: Session):
    """Test Y: Once linked to an order, the specification cannot be modified through production or review APIs."""
    user = create_test_user(db_session, "user.immutable@jewelmind.com")
    headers = get_auth_headers(user)
    spec, _, _ = create_specification_tree(db_session, user, status="approved")

    req = ProductionOrderCreateFromSpecification(
        specification_id=spec.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
    )
    order = production_service.create_order_from_specification(db_session, user.id, req)

    # Attempt to modify the approved specification via review API
    patch_payload = {
        "category": "brooch",
        "fabrication_notes": "Attempting unauthorized modification of approved specification",
    }
    res_patch = client.patch(f"/api/v1/production-specifications/{spec.id}", json=patch_payload, headers=headers)
    assert res_patch.status_code == 409  # Conflict: approved specification is immutable!

    # Attempt to change render on order via production order update
    another_render_id = str(uuid.uuid4())
    update_payload = {
        "render_id": another_render_id,
    }
    res_update = client.patch(f"/api/v1/production/orders/{order.id}", json=update_payload, headers=headers)
    assert res_update.status_code == 400
    msg = res_update.json().get("error", {}).get("message", "").lower()
    assert "render" in msg or "specification" in msg


def test_z_cross_user_order_and_schedule_isolation(client: TestClient, db_session: Session):
    """Test Z: Users cannot view or schedule production orders belonging to other tenants."""
    user_a = create_test_user(db_session, "tenant.a@jewelmind.com")
    user_b = create_test_user(db_session, "tenant.b@jewelmind.com")
    headers_b = get_auth_headers(user_b)

    spec_a, _, _ = create_specification_tree(db_session, user_a, status="approved")
    req = ProductionOrderCreateFromSpecification(
        specification_id=spec_a.id,
        quantity=1,
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
    )
    order_a = production_service.create_order_from_specification(db_session, user_a.id, req)

    # Tenant B tries to get Tenant A's order -> 404
    res_get = client.get(f"/api/v1/production/orders/{order_a.id}", headers=headers_b)
    assert res_get.status_code == 404

    # Tenant B tries to schedule Tenant A's order -> empty or infeasible
    opt_req = {
        "order_ids": [str(order_a.id)],
        "horizon_days": 10,
    }
    res_opt = client.post("/api/v1/production/optimize", json=opt_req, headers=headers_b)
    assert res_opt.status_code == 200
    data = res_opt.json()
    assert data["metrics"]["total_orders_scheduled"] == 0
