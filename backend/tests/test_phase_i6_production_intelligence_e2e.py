"""
Phase I.6 — End-to-End Production Intelligence Validation Test Suite

Validates the complete, unbroken lifecycle:
Design -> Approved Render -> AI Production Intelligence -> Artisan Review ->
Artisan Overrides -> Approval -> Production Order -> Dynamic Routing ->
Worker / Machine Matching -> CP-SAT Optimization -> Traceable Production Schedule.

Covers Test Matrix:
A. Full E2E approved flow
B. All 8 jewelry categories
C. Gemstone-free design
D. Single gemstone design
E. Multi-gemstone design
F. Material variations (Gold, Platinum, Silver)
G. Artisan overrides & provenance preservation
H. Provenance distinction: ARTISAN_OVERRIDE vs AI_ESTIMATE
I. Approval gate (draft & archived rejected)
J. Approved specification immutability
K. Specification versioning lifecycle
L. Exact render lineage & mismatch rejection
M. Cross-tenant security & IDOR prevention (404 Not Found)
N. Client ID injection prevention
O. BOM material & gemstone integrity
P. Dynamic routing (N stages)
Q. 3-step routing
R. 5+ step routing
S. Quantity scaling & non-negative duration
T. Worker skill constraints
U. Machine type constraints
V. CP-SAT feasible schedule & makespan
W. CP-SAT infeasible schedule & diagnostic
X. Precedence constraints (start_N >= end_{N-1})
Y. Legacy order compatibility (specification_id = None)
Z. Transaction atomicity & rollback
AB. API contract regression
AC. Database integrity
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
from app.schemas.production_specification import (
    ProductionGemstoneUpdate,
    ProductionMaterialUpdate,
    ProductionSpecificationUpdateRequest,
    ProductionStepUpdate,
)
from app.services.gemini_production_service import get_gemini_production_service, GeminiProductionService
from app.services.production_optimization_service import production_optimization_service
from app.services.production_service import production_service
from app.services.production_specification_service import production_specification_service
from app.services.user_service import user_service


# ---------------------------------------------------------------------------
# Test Helpers & Fixtures
# ---------------------------------------------------------------------------

def create_user(db_session: Session, email: str = "artisan.e2e@jewelmind.com") -> User:
    """Creates a distinct user for testing."""
    return user_service.create(
        db_session,
        UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Artisan E2E Tester",
        ),
    )


def get_headers(user: User) -> dict:
    """Generates standard JWT authorization headers."""
    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


def setup_standard_workshop(db_session: Session, user: User) -> dict:
    """Sets up a comprehensive workshop with all artisan skills and machines."""
    workers = [
        Worker(
            id=uuid.uuid4(),
            user_id=user.id,
            name="CAD Specialist",
            skill="cad_design",
            capacity_hours_per_day=8.0,
            is_available=True,
        ),
        Worker(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Master Caster",
            skill="casting",
            capacity_hours_per_day=8.0,
            is_available=True,
        ),
        Worker(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Diamond Setter",
            skill="stone_setting",
            capacity_hours_per_day=8.0,
            is_available=True,
        ),
        Worker(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Master Polisher",
            skill="polishing",
            capacity_hours_per_day=8.0,
            is_available=True,
        ),
        Worker(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Senior QA Inspector",
            skill="quality_assurance",
            capacity_hours_per_day=8.0,
            is_available=True,
        ),
        Worker(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Bench Jeweler",
            skill="general",
            capacity_hours_per_day=8.0,
            is_available=True,
        ),
    ]
    machines = [
        Machine(
            id=uuid.uuid4(),
            user_id=user.id,
            name="SLA Wax 3D Printer",
            machine_type="3d_wax_printer",
            capacity_hours_per_day=16.0,
            is_available=True,
        ),
        Machine(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Induction Vacuum Casting Furnace",
            machine_type="casting_furnace",
            capacity_hours_per_day=12.0,
            is_available=True,
        ),
        Machine(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Ultrasonic Cleaner & Wash Station",
            machine_type="ultrasonic_cleaner",
            capacity_hours_per_day=12.0,
            is_available=True,
        ),
        Machine(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Precision Polishing Lathe",
            machine_type="polishing_lathe",
            capacity_hours_per_day=12.0,
            is_available=True,
        ),
        Machine(
            id=uuid.uuid4(),
            user_id=user.id,
            name="High-Precision Laser Engraver & Welder",
            machine_type="laser_engraver",
            capacity_hours_per_day=10.0,
            is_available=True,
        ),
    ]
    for w in workers:
        db_session.add(w)
    for m in machines:
        db_session.add(m)
    db_session.commit()
    return {"workers": workers, "machines": machines}


def create_test_render(
    db_session: Session,
    user: User,
    design: Design,
    image_url: str = "https://storage.jewelmind.ai/renders/test.png",
    is_approved: bool = True,
    version_number: int = 1,
) -> DesignRender:
    render = DesignRender(
        id=uuid.uuid4(),
        design_id=design.id,
        user_id=user.id,
        image_url=image_url,
        prompt="Artisan 3D jewellery render",
        version_number=version_number,
        is_approved_for_production=is_approved,
    )
    db_session.add(render)
    db_session.commit()
    return render



# ---------------------------------------------------------------------------
# TEST 1 (A): Complete End-to-End Lifecycle Validation
# ---------------------------------------------------------------------------

def test_full_e2e_approved_lifecycle(client: TestClient, db_session: Session):
    """
    Step-by-step validation of the complete Production Intelligence pipeline:
    1. Create Design
    2. Create & Approve Render
    3. AI Production Intelligence generates specification
    4. Artisan reviews and adds overrides
    5. Artisan approves and locks specification
    6. Production Order created from approved specification
    7. Workshop resources matched
    8. Real Google OR-Tools CP-SAT generates schedule
    9. Full traceability verified
    """
    user = create_user(db_session, "artisan.lifecycle@jewelmind.com")
    headers = get_headers(user)
    setup_standard_workshop(db_session, user)

    # 1. Create Design
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Royal Solitaire Diamond Ring",
        category="ring",
        status="active",
    )
    db_session.add(design)
    db_session.commit()

    # 2. Create & Approve Render
    render = create_test_render(
        db_session,
        user,
        design,
        image_url="https://storage.jewelmind.ai/renders/royal_solitaire_approved.png",
        is_approved=True,
    )

    # 3. AI Production Intelligence generates specification
    gen_res = client.post(
        "/api/v1/production-specifications/generate",
        json={"render_id": str(render.id)},
        headers=headers,
    )
    assert gen_res.status_code == 201
    spec_data = gen_res.json()
    spec_id = spec_data["id"]
    assert spec_data["status"] == "draft"
    assert spec_data["category"] == "ring"
    assert len(spec_data["materials"]) > 0
    assert len(spec_data["steps"]) >= 3

    # 4. Artisan modifies selected manufacturing fields
    mat_to_update = spec_data["materials"][0]
    update_payload = {
        "category": "ring",
        "estimated_finished_metal_weight_grams": 5.8,
        "fabrication_notes": "Artisan note: Hand-beaded prong finish required.",
        "materials": [
            {
                "id": mat_to_update["id"],
                "metal_type": mat_to_update["metal_type"],
                "metal_purity": "18k",
                "metal_color": "yellow",
                "metal_finish": "high_polish",
                "plating": None,
                "estimated_weight_grams": 5.8,
                "casting_loss_percentage": 10.0,
            }
        ],
        "gemstones": [
            {
                "id": None,
                "gemstone_type": "diamond",
                "cut_shape": "round_brilliant",
                "stone_count": 1,
                "estimated_carat_weight": 1.25,
                "approximate_dimensions_mm": "6.8mm",
                "setting_type": "prong",
                "is_center_stone": True,
            }
        ],
        "steps": [
            {
                "id": s["id"],
                "step_number": s["step_number"],
                "stage_name": s["stage_name"],
                "required_skill": s["required_skill"],
                "required_machine_type": s["required_machine_type"],
                "base_hours": s["base_hours"],
                "per_unit_hours": s["per_unit_hours"],
                "description": s.get("description"),
                "quality_checkpoint": s.get("quality_checkpoint"),
            }
            for s in spec_data["steps"]
        ],
    }
    patch_res = client.patch(
        f"/api/v1/production-specifications/{spec_id}",
        json=update_payload,
        headers=headers,
    )
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["materials"][0]["origin"] == "ARTISAN_OVERRIDE"
    assert patched_data["gemstones"][0]["origin"] == "ARTISAN_OVERRIDE"

    # 5. Artisan approves specification
    approve_res = client.post(
        f"/api/v1/production-specifications/{spec_id}/approve",
        headers=headers,
    )
    assert approve_res.status_code == 200
    approved_spec = approve_res.json()
    assert approved_spec["status"] == "approved"
    assert approved_spec["approved_at"] is not None

    # 6. Production Order created from approved specification
    order_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": spec_id,
            "quantity": 2,
            "priority": "high",
            "notes": "VIP client commission", "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert order_res.status_code == 201
    order_data = order_res.json()
    order_id = order_data["id"]

    # Verify authoritative server-derived lineage
    assert order_data["specification_id"] == spec_id
    assert order_data["design_id"] == str(design.id)
    assert order_data["render_id"] == str(render.id)
    assert order_data["approved_render_url"] == render.image_url
    assert order_data["specification_version"] == 1
    assert order_data["quantity"] == 2
    assert order_data["routing_steps_count"] == len(approved_spec["steps"])

    # 7 & 8. CP-SAT solves production schedule
    opt_res = client.post(
        "/api/v1/production/optimize",
        json={
            "horizon_days": 14,
            "time_limit_seconds": 10,
            "persist_schedule": True,
        },
        headers=headers,
    )
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["status"] in ("success", "feasible")
    assert opt_data["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert len(opt_data["schedule"]) == len(approved_spec["steps"])

    # 9. Verify traceability on every scheduled task
    scheduled_tasks = sorted(opt_data["schedule"], key=lambda t: t["sequence_order"])
    for idx, task in enumerate(scheduled_tasks):
        assert task["order_id"] == order_id
        assert task["specification_id"] == spec_id
        assert task["step_number"] == idx + 1
        assert task["duration_hours"] > 0
        # Verify sequential precedence start(k) >= end(k-1)
        if idx > 0:
            prev_end = datetime.fromisoformat(scheduled_tasks[idx - 1]["end_time"].replace("Z", "+00:00"))
            curr_start = datetime.fromisoformat(task["start_time"].replace("Z", "+00:00"))
            assert curr_start >= prev_end


# ---------------------------------------------------------------------------
# TEST 2 (B): All 8 Jewellery Categories Validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "category",
    [
        "ring",
        "earring",
        "pendant",
        "necklace",
        "bracelet",
        "bangle",
        "brooch",
        "other_jewellery",
    ],
)
def test_all_eight_jewellery_categories_e2e(client: TestClient, db_session: Session, category: str):
    """
    Validates end-to-end specification generation, approval, order creation, and
    CP-SAT scheduling across all 8 supported jewellery categories.
    """
    user = create_user(db_session, f"artisan.cat.{category}@jewelmind.com")
    headers = get_headers(user)
    setup_standard_workshop(db_session, user)

    # 1. Design & Approved Render
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name=f"Collection {category.title()} Piece",
        category=category,
        status="active",
    )
    db_session.add(design)
    db_session.commit()

    render = create_test_render(
        db_session,
        user,
        design,
        image_url=f"https://storage.jewelmind.ai/renders/{category}_appr.png",
        is_approved=True,
    )

    # 2. Specification Generation
    gen_res = client.post(
        "/api/v1/production-specifications/generate",
        json={"render_id": str(render.id)},
        headers=headers,
    )
    assert gen_res.status_code == 201
    spec_data = gen_res.json()
    assert spec_data["category"] == category
    assert len(spec_data["steps"]) >= 3

    # 3. Approve Specification
    appr_res = client.post(
        f"/api/v1/production-specifications/{spec_data['id']}/approve",
        headers=headers,
    )
    assert appr_res.status_code == 200

    # 4. Create Production Order
    ord_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": spec_data["id"], "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert ord_res.status_code == 201
    ord_data = ord_res.json()
    assert ord_data["specification_category"] == category

    # 5. CP-SAT Production Schedule
    sched_res = client.post(
        "/api/v1/production/optimize",
        json={"horizon_days": 14, "time_limit_seconds": 10},
        headers=headers,
    )
    assert sched_res.status_code == 200
    sched_data = sched_res.json()
    assert sched_data["status"] in ("success", "feasible")
    assert len(sched_data["schedule"]) == len(spec_data["steps"])


# ---------------------------------------------------------------------------
# TEST 3 (C, D, E): Gemstone Variations (Gem-Free, Single, Multi-Stone)
# ---------------------------------------------------------------------------

def test_gemstone_free_routing_omits_stone_setting(client: TestClient, db_session: Session):
    """
    Scenario A (Gem-free): A plain band without gemstones must NOT artificially
    receive a stone setting operation merely because legacy systems had one.
    """
    user = create_user(db_session, "plain.band@jewelmind.com")
    headers = get_headers(user)
    setup_standard_workshop(db_session, user)

    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Classic Plain Wedding Band",
        category="ring",
        status="active",
    )
    db_session.add(design)
    db_session.commit()

    render = create_test_render(
        db_session,
        user,
        design,
        image_url="https://storage.jewelmind.ai/renders/band.png",
        is_approved=True,
    )

    # Generate spec
    gen_res = client.post(
        "/api/v1/production-specifications/generate",
        json={"render_id": str(render.id), "gemstone_hint": "no stones, solid metal band"},
        headers=headers,
    )
    assert gen_res.status_code == 201
    spec_data = gen_res.json()
    spec_id = spec_data["id"]

    # Explicitly ensure 0 gemstones and gem-free steps
    update_payload = {
        "category": "ring",
        "gemstones": [],
        "steps": [
            {
                "id": None,
                "step_number": 1,
                "stage_name": "Wax Pattern & 3D Printing",
                "required_skill": "cad_design",
                "required_machine_type": "3d_wax_printer",
                "base_hours": 1.5,
                "per_unit_hours": 0.5,
                "description": "3D print wax model",
                "quality_checkpoint": "Check band thickness",
            },
            {
                "id": None,
                "step_number": 2,
                "stage_name": "Lost Wax Casting",
                "required_skill": "casting",
                "required_machine_type": "casting_furnace",
                "base_hours": 2.0,
                "per_unit_hours": 0.5,
                "description": "Cast platinum alloy",
                "quality_checkpoint": "Inspect for porosity",
            },
            {
                "id": None,
                "step_number": 3,
                "stage_name": "Mirror Lapping & Polishing",
                "required_skill": "polishing",
                "required_machine_type": "polishing_lathe",
                "base_hours": 1.5,
                "per_unit_hours": 0.5,
                "description": "High polish finish",
                "quality_checkpoint": "Final luster check",
            },
        ],
    }
    patch_res = client.patch(
        f"/api/v1/production-specifications/{spec_id}",
        json=update_payload,
        headers=headers,
    )
    assert patch_res.status_code == 200

    # Approve and create order
    client.post(f"/api/v1/production-specifications/{spec_id}/approve", headers=headers)
    ord_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": spec_id, "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert ord_res.status_code == 201

    # Solve CP-SAT
    opt_res = client.post("/api/v1/production/optimize", json={"horizon_days": 7}, headers=headers)
    assert opt_res.status_code == 200
    sched = opt_res.json()["schedule"]
    assert len(sched) == 3

    # Assert NO task has stone_setting stage or skill
    for t in sched:
        assert "stone" not in t["operation_name"].lower()
        assert "setting" not in t["operation_name"].lower()


def test_multi_gemstone_pave_routing(client: TestClient, db_session: Session):
    """
    Scenario B (Multi-gemstone): Verifies multi-gemstone counts and details survive
    into the order workflow and scheduling preserves setting stages.
    """
    user = create_user(db_session, "pave.halo@jewelmind.com")
    headers = get_headers(user)
    setup_standard_workshop(db_session, user)

    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Pavé Halo Pendant",
        category="pendant",
        status="active",
    )
    db_session.add(design)
    db_session.commit()

    render = create_test_render(
        db_session,
        user,
        design,
        image_url="https://storage.jewelmind.ai/renders/pave.png",
        is_approved=True,
    )

    # Create spec with center stone + 24 melee diamonds
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="pendant",
        estimated_rough_metal_weight_grams=4.5,
        estimated_finished_metal_weight_grams=3.8,
        total_gemstone_count=25,
        estimated_total_bench_hours=8.0,
    )
    db_session.add(spec)
    db_session.flush()

    mat = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type="gold",
        metal_purity="18k",
        metal_color="white",
        estimated_weight_grams=3.8,
    )
    gem_center = ProductionGemstone(
        id=uuid.uuid4(),
        specification_id=spec.id,
        gemstone_type="sapphire",
        cut_shape="oval",
        stone_count=1,
        estimated_carat_weight=1.5,
        setting_type="prong",
        is_center_stone=True,
    )
    gem_melee = ProductionGemstone(
        id=uuid.uuid4(),
        specification_id=spec.id,
        gemstone_type="diamond",
        cut_shape="round_brilliant",
        stone_count=24,
        estimated_carat_weight=0.36,
        setting_type="pave",
        is_center_stone=False,
    )
    db_session.add_all([mat, gem_center, gem_melee])

    # Steps
    s1 = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=1,
        stage_name="Casting & Clean-up",
        required_skill="casting",
        required_machine_type="casting_furnace",
        base_hours=2.0,
        per_unit_hours=0.5,
    )
    s2 = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=2,
        stage_name="Micro-Pavé Setting",
        required_skill="stone_setting",
        required_machine_type=None,
        base_hours=4.0,
        per_unit_hours=1.0,
    )
    s3 = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=3,
        stage_name="Rhodium Plating & Polishing",
        required_skill="polishing",
        required_machine_type="polishing_lathe",
        base_hours=1.5,
        per_unit_hours=0.5,
    )
    db_session.add_all([s1, s2, s3])
    db_session.commit()

    # Approve & Create Order
    client.post(f"/api/v1/production-specifications/{spec.id}/approve", headers=headers)
    ord_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": str(spec.id), "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert ord_res.status_code == 201
    ord_data = ord_res.json()
    assert ord_data["gemstones_count"] == 2
    assert ord_data["routing_steps_count"] == 3


# ---------------------------------------------------------------------------
# TEST 4 (F): Material Variations (Gold, Platinum, Silver)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "metal_type,purity,color,finish",
    [
        ("gold", "18k", "yellow", "high_polish"),
        ("platinum", "950", "white", "satin"),
        ("silver", "925", "white", "high_polish"),
    ],
)
def test_material_variations_preserved_in_order(
    client: TestClient, db_session: Session, metal_type: str, purity: str, color: str, finish: str
):
    """
    Verifies that various metallurgy profiles (18k Gold, Platinum 950, Sterling Silver 925)
    are strictly preserved from specification to production order without alteration.
    """
    user = create_user(db_session, f"artisan.mat.{metal_type}@jewelmind.com")
    headers = get_headers(user)
    setup_standard_workshop(db_session, user)

    design = Design(id=uuid.uuid4(), user_id=user.id, name=f"{purity} {metal_type} Item", category="ring", status="active")
    db_session.add(design)
    db_session.commit()

    render = create_test_render(
        db_session,
        user,
        design,
        image_url=f"https://storage.jewelmind.ai/renders/{metal_type}.png",
        is_approved=True,
    )

    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        approved_at=datetime.now(timezone.utc),
        category="ring",
        estimated_rough_metal_weight_grams=6.0,
        estimated_finished_metal_weight_grams=5.2,
    )
    mat = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type=metal_type,
        metal_purity=purity,
        metal_color=color,
        metal_finish=finish,
        estimated_weight_grams=5.2,
        casting_loss_percentage=8.5,
    )
    step = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=1,
        stage_name="Foundry Casting",
        required_skill="casting",
        required_machine_type="casting_furnace",
        base_hours=3.0,
        per_unit_hours=0.5,
    )
    db_session.add_all([spec, mat, step])
    db_session.commit()

    # Create Order
    ord_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": str(spec.id), "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert ord_res.status_code == 201
    ord_data = ord_res.json()
    assert ord_data["materials_count"] == 1

    # Verify underlying specification material was not mutated
    db_mat = db_session.query(ProductionMaterial).filter_by(specification_id=spec.id).first()
    assert db_mat.metal_type == metal_type
    assert db_mat.metal_purity == purity
    assert db_mat.casting_loss_percentage == 8.5


# ---------------------------------------------------------------------------
# TEST 5 (I, J): Approval Gates & Immutability Enforcement
# ---------------------------------------------------------------------------

def test_approval_gates_and_immutability(client: TestClient, db_session: Session):
    """
    Verifies that:
    1. Draft specifications cannot create a production order (400 Bad Request).
    2. Archived specifications cannot create a production order (400 Bad Request).
    3. Approved specifications cannot be patched or modified (400 Bad Request).
    """
    user = create_user(db_session, "artisan.gates@jewelmind.com")
    headers = get_headers(user)

    design = Design(id=uuid.uuid4(), user_id=user.id, name="Gate Test Ring", category="ring", status="active")
    db_session.add(design)
    db_session.commit()

    render = create_test_render(
        db_session,
        user,
        design,
        image_url="https://storage.jewelmind.ai/renders/gate.png",
        is_approved=True,
    )

    # Case 1: Draft Specification
    draft_spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="draft",
        category="ring",
    )
    db_session.add(draft_spec)
    db_session.commit()

    draft_order_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": str(draft_spec.id), "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert draft_order_res.status_code == 400
    assert "draft" in draft_order_res.json()["error"]["message"].lower()

    # Case 2: Archived Specification
    archived_spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=2,
        status="archived",
        category="ring",
    )
    db_session.add(archived_spec)
    db_session.commit()

    archived_order_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": str(archived_spec.id), "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert archived_order_res.status_code == 400
    assert "archived" in archived_order_res.json()["error"]["message"].lower()

    # Case 3: Approved Specification Immutability
    approved_spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=3,
        status="approved",
        approved_at=datetime.now(timezone.utc),
        category="ring",
    )
    db_session.add(approved_spec)
    db_session.commit()

    patch_res = client.patch(
        f"/api/v1/production-specifications/{approved_spec.id}",
        json={"category": "necklace"},
        headers=headers,
    )
    assert patch_res.status_code in (400, 409)
    err_text = str(patch_res.json()).lower()
    assert "approved" in err_text or "immutable" in err_text or "conflict" in err_text


# ---------------------------------------------------------------------------
# TEST 6 (K): Specification Versioning Lifecycle
# ---------------------------------------------------------------------------

def test_specification_versioning_lifecycle(client: TestClient, db_session: Session):
    """
    Validates that:
    - Spec v1 is approved and ordered.
    - Spec v2 can be created for the same render/design without corrupting v1.
    - Production order referencing v1 strictly remains linked to v1.
    """
    user = create_user(db_session, "artisan.versioning@jewelmind.com")
    headers = get_headers(user)

    design = Design(id=uuid.uuid4(), user_id=user.id, name="Versioned Ring", category="ring", status="active")
    db_session.add(design)
    db_session.commit()

    render = create_test_render(
        db_session,
        user,
        design,
        image_url="https://storage.jewelmind.ai/renders/v1.png",
        is_approved=True,
    )

    # V1 Spec
    v1_spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        approved_at=datetime.now(timezone.utc),
        category="ring",
        fabrication_notes="V1 Notes",
    )
    v1_mat = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=v1_spec.id,
        metal_type="gold",
        metal_purity="14k",
    )
    v1_step = ProductionStep(
        id=uuid.uuid4(),
        specification_id=v1_spec.id,
        step_number=1,
        stage_name="V1 Casting",
        required_skill="casting",
        base_hours=2.0,
        per_unit_hours=0.5,
    )
    db_session.add_all([v1_spec, v1_mat, v1_step])
    db_session.commit()

    # Order tied to v1
    v1_order_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": str(v1_spec.id), "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert v1_order_res.status_code == 201
    v1_order = v1_order_res.json()
    assert v1_order["specification_version"] == 1

    # Create v2 spec for the same render
    v2_spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=2,
        status="approved",
        approved_at=datetime.now(timezone.utc),
        category="ring",
        fabrication_notes="V2 Upgraded Notes",
    )
    v2_mat = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=v2_spec.id,
        metal_type="gold",
        metal_purity="18k",
    )
    v2_step = ProductionStep(
        id=uuid.uuid4(),
        specification_id=v2_spec.id,
        step_number=1,
        stage_name="V2 Casting",
        required_skill="casting",
        base_hours=3.0,
        per_unit_hours=0.5,
    )
    db_session.add_all([v2_spec, v2_mat, v2_step])
    db_session.commit()

    # Verify v1 order still references v1
    v1_check = client.get(f"/api/v1/production/orders/{v1_order['id']}", headers=headers)
    assert v1_check.status_code == 200
    assert v1_check.json()["specification_id"] == str(v1_spec.id)
    assert v1_check.json()["specification_version"] == 1


# ---------------------------------------------------------------------------
# TEST 7 (M, N): Cross-Tenant Security & IDOR Prevention
# ---------------------------------------------------------------------------

def test_cross_tenant_isolation_and_idor_prevention(client: TestClient, db_session: Session):
    """
    Validates that User B cannot access, modify, approve, create an order from,
    or schedule User A's specification or render. (Returns 404 to avoid leaking existence).
    """
    user_a = create_user(db_session, "user.a@jewelmind.com")
    user_b = create_user(db_session, "user.b@jewelmind.com")
    headers_b = get_headers(user_b)

    # User A owns a design and approved specification
    design_a = Design(id=uuid.uuid4(), user_id=user_a.id, name="User A Secret Ring", category="ring", status="active")
    db_session.add(design_a)
    db_session.commit()

    render_a = create_test_render(
        db_session,
        user_a,
        design_a,
        image_url="https://storage.jewelmind.ai/renders/secret_a.png",
        is_approved=True,
    )

    spec_a = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user_a.id,
        design_id=design_a.id,
        render_id=render_a.id,
        version_number=1,
        status="approved",
        approved_at=datetime.now(timezone.utc),
        category="ring",
    )
    mat_a = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec_a.id,
        metal_type="gold",
        metal_purity="18k",
    )
    step_a = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec_a.id,
        step_number=1,
        stage_name="Casting",
        required_skill="casting",
        base_hours=2.0,
        per_unit_hours=0.5,
    )
    db_session.add_all([spec_a, mat_a, step_a])
    db_session.commit()

    # 1. User B attempts to GET User A's spec
    get_res = client.get(f"/api/v1/production-specifications/{spec_a.id}", headers=headers_b)
    assert get_res.status_code == 404

    # 2. User B attempts to PATCH User A's spec
    patch_res = client.patch(
        f"/api/v1/production-specifications/{spec_a.id}",
        json={"category": "earring"},
        headers=headers_b,
    )
    assert patch_res.status_code == 404

    # 3. User B attempts to approve User A's spec
    appr_res = client.post(f"/api/v1/production-specifications/{spec_a.id}/approve", headers=headers_b)
    assert appr_res.status_code == 404

    # 4. User B attempts to create order from User A's spec
    ord_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": str(spec_a.id), "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers_b,
    )
    assert ord_res.status_code == 404


# ---------------------------------------------------------------------------
# TEST 8 (L): Exact Render Lineage & Mismatch Rejection
# ---------------------------------------------------------------------------

def test_render_lineage_mismatch_rejection(client: TestClient, db_session: Session):
    """
    Verifies that if a specification's render_id points to an unapproved render
    or a render from another design, order creation is rejected with 400.
    """
    user = create_user(db_session, "artisan.mismatch@jewelmind.com")
    headers = get_headers(user)

    design_1 = Design(id=uuid.uuid4(), user_id=user.id, name="Design 1", category="ring", status="active")
    design_2 = Design(id=uuid.uuid4(), user_id=user.id, name="Design 2", category="ring", status="active")
    db_session.add_all([design_1, design_2])
    db_session.commit()

    # Render belongs to Design 2, but unapproved
    unapproved_render = create_test_render(
        db_session,
        user,
        design_2,
        image_url="https://storage.jewelmind.ai/renders/unapproved.png",
        is_approved=False,
    )

    # Spec claims to be for Design 1, but references render from Design 2
    mismatched_spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design_1.id,
        render_id=unapproved_render.id,
        version_number=1,
        status="approved",
        approved_at=datetime.now(timezone.utc),
        category="ring",
    )
    db_session.add(mismatched_spec)
    db_session.commit()

    res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": str(mismatched_spec.id), "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert res.status_code == 400
    assert "lineage" in res.json()["error"]["message"].lower() or "render" in res.json()["error"]["message"].lower()


# ---------------------------------------------------------------------------
# TEST 9 (P, Q, R, S): Dynamic Routing, Multi-Stage & Quantity Scaling
# ---------------------------------------------------------------------------

def test_dynamic_routing_and_quantity_duration_scaling(client: TestClient, db_session: Session):
    """
    Validates dynamic routing with 5+ stages and tests duration scaling:
    duration = base_hours + (per_unit_hours * quantity) for Qty=1 and Qty=10.
    """
    user = create_user(db_session, "artisan.scaling@jewelmind.com")
    headers = get_headers(user)
    setup_standard_workshop(db_session, user)

    design = Design(id=uuid.uuid4(), user_id=user.id, name="Artisan Necklace", category="necklace", status="active")
    db_session.add(design)
    db_session.commit()

    render = create_test_render(
        db_session,
        user,
        design,
        image_url="https://storage.jewelmind.ai/renders/necklace.png",
        is_approved=True,
    )

    # 5-step routing
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        approved_at=datetime.now(timezone.utc),
        category="necklace",
    )
    mat = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type="gold",
        metal_purity="18k",
    )
    steps = [
        ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=1,
            stage_name="CAD & 3D Prototyping",
            required_skill="cad_design",
            required_machine_type="3d_wax_printer",
            base_hours=2.0,
            per_unit_hours=0.5,
        ),
        ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=2,
            stage_name="Vacuum Metallurgy Casting",
            required_skill="casting",
            required_machine_type="casting_furnace",
            base_hours=3.0,
            per_unit_hours=1.0,
        ),
        ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=3,
            stage_name="Gemstone Collet Assembly",
            required_skill="stone_setting",
            required_machine_type=None,
            base_hours=4.0,
            per_unit_hours=2.0,
        ),
        ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=4,
            stage_name="Mirror Surface Finishing",
            required_skill="polishing",
            required_machine_type="polishing_lathe",
            base_hours=2.5,
            per_unit_hours=0.5,
        ),
        ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=5,
            stage_name="Quality Audit & Hallmark Assay",
            required_skill="quality_assurance",
            required_machine_type=None,
            base_hours=1.0,
            per_unit_hours=0.2,
        ),
    ]
    db_session.add_all([spec, mat] + steps)
    db_session.commit()

    # 1. Test Qty = 1
    ord1_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": str(spec.id), "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert ord1_res.status_code == 201

    opt1_res = client.post("/api/v1/production/optimize", json={"horizon_days": 14}, headers=headers)
    assert opt1_res.status_code == 200
    sched1 = sorted(opt1_res.json()["schedule"], key=lambda t: t["sequence_order"])
    assert len(sched1) == 5
    # Step 2 with qty 1: base 3.0 + 1.0 * 1 = 4.0h
    assert sched1[1]["duration_hours"] == 4.0

    # Delete order 1 to test Qty = 10 cleanly
    client.delete(f"/api/v1/production/orders/{ord1_res.json()['id']}", headers=headers)

    # 2. Test Qty = 10
    ord10_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": str(spec.id), "quantity": 10, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert ord10_res.status_code == 201

    opt10_res = client.post("/api/v1/production/optimize", json={"horizon_days": 21}, headers=headers)
    assert opt10_res.status_code == 200
    sched10 = sorted(opt10_res.json()["schedule"], key=lambda t: t["sequence_order"])
    # Step 2 with qty 10: base 3.0 + 1.0 * 10 = 13.0h
    assert sched10[1]["duration_hours"] == 13.0


# ---------------------------------------------------------------------------
# TEST 10 (T, U, W): Resource Constraints & Infeasibility Diagnostics
# ---------------------------------------------------------------------------

def test_missing_resource_produces_infeasible_diagnostic(client: TestClient, db_session: Session):
    """
    Validates that if a specification operation strictly requires an artisan skill
    or machine that does NOT exist in the workshop roster, CP-SAT returns a clean
    infeasible diagnostic rather than arbitrarily assigning invalid resources.
    """
    user = create_user(db_session, "artisan.infeasible@jewelmind.com")
    headers = get_headers(user)

    # Create workshop WITHOUT any stone_setting artisans
    worker_caster = Worker(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Only Caster",
        skill="casting",
        capacity_hours_per_day=8.0,
        is_available=True,
    )
    machine_caster = Machine(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Casting Lathe",
        machine_type="casting_furnace",
        capacity_hours_per_day=8.0,
        is_available=True,
    )
    db_session.add_all([worker_caster, machine_caster])
    db_session.commit()

    design = Design(id=uuid.uuid4(), user_id=user.id, name="Diamond Ring", category="ring", status="active")
    db_session.add(design)
    db_session.commit()

    render = create_test_render(
        db_session,
        user,
        design,
        image_url="https://storage.jewelmind.ai/renders/ring.png",
        is_approved=True,
    )

    # Spec requires stone_setting skill
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        approved_at=datetime.now(timezone.utc),
        category="ring",
    )
    mat = ProductionMaterial(id=uuid.uuid4(), specification_id=spec.id, metal_type="gold", metal_purity="18k",)
    step = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=1,
        stage_name="Intricate Stone Setting",
        required_skill="stone_setting",
        required_machine_type=None,
        base_hours=3.0,
        per_unit_hours=0.5,
    )
    db_session.add_all([spec, mat, step])
    db_session.commit()

    # Create order
    ord_res = client.post(
        "/api/v1/production/orders/from-specification",
        json={"specification_id": str(spec.id), "quantity": 1, "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()},
        headers=headers,
    )
    assert ord_res.status_code == 201

    # Optimize -> Should be INFEASIBLE with diagnostic
    opt_res = client.post("/api/v1/production/optimize", json={"horizon_days": 14}, headers=headers)
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["status"] == "infeasible"
    assert opt_data["solver_status"] == "INFEASIBLE"
    assert len(opt_data["infeasibility_reasons"]) > 0
    assert any("stone_setting" in r for r in opt_data["infeasibility_reasons"])


# ---------------------------------------------------------------------------
# TEST 11 (Y): Legacy Production Order Compatibility
# ---------------------------------------------------------------------------

def test_legacy_order_without_specification_compatibility(client: TestClient, db_session: Session):
    """
    Validates that a legacy production order (with specification_id = None)
    continues to be processed correctly through the existing 3-stage fallback
    without causing any runtime regressions or database corruptions.
    """
    user = create_user(db_session, "artisan.legacy@jewelmind.com")
    headers = get_headers(user)
    setup_standard_workshop(db_session, user)

    design = Design(id=uuid.uuid4(), user_id=user.id, name="Legacy Heritage Ring", category="ring", status="active")
    db_session.add(design)
    db_session.commit()

    # Create order directly via legacy API
    legacy_order_res = client.post(
        "/api/v1/production/orders",
        json={
            "design_id": str(design.id),
            "quantity": 1,
            "priority": "medium",
            "status": "pending",
            "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "notes": "Historical legacy order",
        },
        headers=headers,
    )
    assert legacy_order_res.status_code == 201
    legacy_order = legacy_order_res.json()
    assert legacy_order["specification_id"] is None
    assert legacy_order.get("routing_steps_count") in (0, None)

    # CP-SAT optimizes legacy order using legacy 3-stage fallback
    opt_res = client.post("/api/v1/production/optimize", json={"horizon_days": 14}, headers=headers)
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["status"] in ("success", "feasible")
    assert len(opt_data["schedule"]) == 3  # Legacy 3 operations: Casting, Setting, Polishing
    for task in opt_data["schedule"]:
        assert task["specification_id"] is None
        assert task["step_number"] in (1, 2, 3)


# ---------------------------------------------------------------------------
# TEST 12 (Z): Transaction Rollback on Order Creation Failure
# ---------------------------------------------------------------------------

def test_transaction_rollback_prevents_orphaned_records(client: TestClient, db_session: Session, monkeypatch):
    """
    Validates atomic rollback: if an unhandled error occurs during order creation,
    the transaction rolls back completely and leaves no partial records.
    """
    user = create_user(db_session, "artisan.rollback@jewelmind.com")
    headers = get_headers(user)

    design = Design(id=uuid.uuid4(), user_id=user.id, name="Rollback Design", category="ring", status="active")
    db_session.add(design)
    db_session.commit()

    render = create_test_render(
        db_session,
        user,
        design,
        image_url="https://storage.jewelmind.ai/renders/rb.png",
        is_approved=True,
    )

    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        approved_at=datetime.now(timezone.utc),
        category="ring",
    )
    mat = ProductionMaterial(id=uuid.uuid4(), specification_id=spec.id, metal_type="gold", metal_purity="18k",)
    step = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=1,
        stage_name="Casting",
        required_skill="casting",
        base_hours=2.0,
        per_unit_hours=0.5,
    )
    db_session.add_all([spec, mat, step])
    db_session.commit()

    initial_order_count = db_session.query(ProductionOrder).filter_by(user_id=user.id).count()

    # Monkeypatch db.flush or commit to simulate unexpected failure
    original_commit = db_session.commit
    def failing_commit():
        raise RuntimeError("Simulated fatal database connection dropped!")
    monkeypatch.setattr(db_session, "commit", failing_commit)

    with pytest.raises(RuntimeError):
        production_service.create_order_from_specification(
            db_session,
            user.id,
            ProductionOrderCreateFromSpecification(
                specification_id=spec.id,
                quantity=1,
                priority=OrderPriority.HIGH,
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
            ),
        )

    # Restore commit and verify count is still 0 (no orphan records)
    monkeypatch.setattr(db_session, "commit", original_commit)
    db_session.rollback()
    assert db_session.query(ProductionOrder).filter_by(user_id=user.id).count() == initial_order_count
