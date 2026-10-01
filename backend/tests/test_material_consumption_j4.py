"""
Phase J.4 — Material Consumption & Wastage Tracking Test Suite
Verifies:
1. Valid metal consumption creation
2. Valid gemstone consumption creation
3. Zero actual quantity acceptance
4. Zero wastage quantity acceptance
5. Valid wastage quantity acceptance
6. Negative actual quantity rejected
7. Negative wastage quantity rejected
8. Wastage greater than actual rejected
9. Invalid / non-existent execution rejected (404)
10. PENDING execution rejected (400)
11. READY execution rejected (400)
12. Valid IN_PROGRESS execution accepted
13. Valid COMPLETED execution accepted
14. Valid specification material linkage accepted & defaults populated
15. Mismatched specification material from another order rejected (400)
16. Valid specification gemstone linkage accepted & defaults populated
17. Mismatched specification gemstone from another order rejected (400)
18. Cross-tenant execution rejected (404)
19. Cross-tenant specification material linkage rejected (404)
20. Cross-tenant order consumption / summary read rejected (404)
21. Consumption correctly linked to order
22. Consumption correctly linked to execution
23. Authoritative specification baseline remains immutable
24. Actual quantity and units stored accurately
25. Wastage quantity and reason stored accurately
26. Order material summary endpoint returns planned / actual / wastage totals
27. Multiple consumption records aggregate correctly in summary
28. Client field injection forbidden (user_id, order_id, execution_id rejected with 422)
29. List execution material consumptions endpoint
30. List order material consumptions endpoint
31. Append-only auditability: multiple draws create new records without rewriting history
32. Execution state machine unaffected by material consumption recording
"""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token
from app.models.design import Design, DesignRender
from app.models.execution import MaterialConsumption, OperationExecution
from app.models.production import Machine, ProductionOrder, Worker
from app.models.specification import (
    ProductionGemstone,
    ProductionMaterial,
    ProductionSpecification,
    ProductionStep,
)
from app.models.user import User
from app.schemas.auth import UserCreate
from app.schemas.execution import (
    ExecutionStatus,
    MaterialConsumptionCreate,
    OperationExecutionTransitionRequest,
)
from app.services.production_execution_service import production_execution_service
from app.services.user_service import user_service


# ==============================================================================
# Helpers & Fixtures
# ==============================================================================

def create_test_user(db: Session, email_prefix: str = "j4_artisan") -> User:
    """Creates a unique test user in the database."""
    unique_email = f"{email_prefix}.{uuid.uuid4().hex[:8]}@jewelmind.atelier"
    return user_service.create(
        db,
        UserCreate(
            email=unique_email,
            password="SecurePassword123!",
            full_name=f"Master Goldsmith {email_prefix.title()}",
        ),
    )


def auth_headers(user: User) -> dict:
    """Generates bearer authorization headers for a user."""
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def setup_order_with_spec(
    db: Session,
    user: User,
    num_steps: int = 2,
    metal_weight: float = 8.5,
    stone_count: int = 1,
) -> tuple[ProductionOrder, list[OperationExecution], ProductionMaterial, ProductionGemstone, ProductionSpecification]:
    """
    Sets up an approved Design, Render, Specification with materials and gemstones,
    ProductionOrder, and initialized OperationExecutions.
    """
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Artisan Diamond Solitaire Ring",
        category="ring",
        status="approved",
    )
    db.add(design)
    db.commit()

    render = DesignRender(
        id=uuid.uuid4(),
        design_id=design.id,
        user_id=user.id,
        version_number=1,
        render_mode="text",
        prompt="18k gold solitaire diamond ring",
        image_url="https://storage.jewelmind.internal/renders/solitaire_j4.png",
        is_approved_for_production=True,
    )
    db.add(render)
    db.commit()

    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        category="ring",
        estimated_rough_metal_weight_grams=metal_weight + 0.8,
        estimated_finished_metal_weight_grams=metal_weight,
        total_gemstone_count=stone_count,
        complexity_rating="moderate",
        approved_at=datetime.now(timezone.utc),
    )
    db.add(spec)
    db.commit()

    material = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type="gold",
        metal_purity="18k",
        metal_color="yellow",
        estimated_weight_grams=metal_weight,
    )
    gemstone = ProductionGemstone(
        id=uuid.uuid4(),
        specification_id=spec.id,
        gemstone_type="diamond",
        cut_shape="round_brilliant",
        stone_count=stone_count,
        estimated_carat_weight=0.75,
    )
    db.add_all([material, gemstone])

    step_defs = [
        ("Casting & Tree Preparation", "casting", "casting_furnace"),
        ("Stone Setting & Collet Mounting", "stone_setting", None),
        ("Hand Polishing & Ultrasonic Clean", "polishing", "ultrasonic_cleaner"),
    ]
    steps: list[ProductionStep] = []
    for i in range(min(num_steps, len(step_defs))):
        name, skill, machine = step_defs[i]
        step = ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=i + 1,
            stage_name=name,
            required_skill=skill,
            required_machine_type=machine,
            base_hours=2.0,
            per_unit_hours=0.5,
        )
        db.add(step)
        steps.append(step)
    db.commit()

    order = ProductionOrder(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        quantity=1,
        priority="high",
        status="in_progress",
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
        specification_id=spec.id,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    executions = production_execution_service.initialize_order_executions(db, user.id, order.id)
    return order, executions, material, gemstone, spec


# ==============================================================================
# 1. Creation Tests
# ==============================================================================

def test_01_valid_metal_consumption(client: TestClient, db_session: Session):
    """Test 1: Valid metal consumption created against IN_PROGRESS execution."""
    user = create_test_user(db_session, "metal_valid")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    # Transition Step 1 to IN_PROGRESS
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "material_type": "METAL",
        "material_name": "18K Yellow Gold Grain",
        "unit": "g",
        "planned_quantity": 8.50,
        "actual_quantity": 8.80,
        "wastage_quantity": 0.30,
        "wastage_reason": "Casting sprue cut & torch loss",
        "notes": "Batch poured at 1040C",
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["material_type"] == "METAL"
    assert data["material_name"] == "18K Yellow Gold Grain"
    assert data["actual_quantity"] == 8.80
    assert data["wastage_quantity"] == 0.30
    assert data["operation_execution_id"] == str(ex.id)
    assert data["production_order_id"] == str(order.id)
    assert data["user_id"] == str(user.id)


def test_02_valid_gemstone_consumption(client: TestClient, db_session: Session):
    """Test 2: Valid gemstone consumption created against IN_PROGRESS execution."""
    user = create_test_user(db_session, "gem_valid")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "material_type": "GEMSTONE",
        "material_name": "Round Brilliant Diamond (VS1/G)",
        "unit": "pcs",
        "planned_quantity": 1.0,
        "actual_quantity": 1.0,
        "wastage_quantity": 0.0,
        "notes": "Center stone prong set without chips",
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["material_type"] == "GEMSTONE"
    assert data["material_name"] == "Round Brilliant Diamond (VS1/G)"
    assert data["actual_quantity"] == 1.0
    assert data["wastage_quantity"] == 0.0


def test_03_zero_actual_quantity(client: TestClient, db_session: Session):
    """Test 3: Zero actual quantity is valid (e.g. non-destructive adjustment step)."""
    user = create_test_user(db_session, "zero_actual")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "material_type": "METAL",
        "material_name": "18K Gold Solder Wire",
        "unit": "g",
        "planned_quantity": 0.2,
        "actual_quantity": 0.0,
        "wastage_quantity": 0.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 201
    assert resp.json()["actual_quantity"] == 0.0


def test_04_zero_wastage(client: TestClient, db_session: Session):
    """Test 4: Zero wastage quantity is valid (perfect recovery)."""
    user = create_test_user(db_session, "zero_wastage")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "material_type": "GEMSTONE",
        "material_name": "Natural Emerald",
        "unit": "pcs",
        "actual_quantity": 2.0,
        "wastage_quantity": 0.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 201
    assert resp.json()["wastage_quantity"] == 0.0


def test_05_valid_wastage(client: TestClient, db_session: Session):
    """Test 5: Valid wastage (wastage <= actual) is recorded properly."""
    user = create_test_user(db_session, "valid_wastage")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "material_type": "METAL",
        "material_name": "Platinum 950",
        "unit": "g",
        "planned_quantity": 10.0,
        "actual_quantity": 10.5,
        "wastage_quantity": 0.5,
        "wastage_reason": "Bench filing and emery paper dust",
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 201
    assert resp.json()["actual_quantity"] == 10.5
    assert resp.json()["wastage_quantity"] == 0.5


# ==============================================================================
# 2. Validation Rules
# ==============================================================================

def test_06_negative_actual_quantity_rejected(client: TestClient, db_session: Session):
    """Test 6: Negative actual quantity is rejected with 422 validation error."""
    user = create_test_user(db_session, "neg_actual")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "material_type": "METAL",
        "material_name": "Gold",
        "unit": "g",
        "actual_quantity": -2.5,
        "wastage_quantity": 0.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 422


def test_07_negative_wastage_rejected(client: TestClient, db_session: Session):
    """Test 7: Negative wastage quantity is rejected with 422 validation error."""
    user = create_test_user(db_session, "neg_wastage")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "material_type": "METAL",
        "material_name": "Gold",
        "unit": "g",
        "actual_quantity": 5.0,
        "wastage_quantity": -0.5,
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 422


def test_08_wastage_greater_than_actual_rejected(client: TestClient, db_session: Session):
    """Test 8: Wastage quantity exceeding actual quantity is rejected."""
    user = create_test_user(db_session, "waste_exceed")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "material_type": "METAL",
        "material_name": "18K Gold",
        "unit": "g",
        "actual_quantity": 4.0,
        "wastage_quantity": 5.0,  # 5.0 > 4.0 invalid!
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code in (400, 422)


def test_09_invalid_execution_rejected(client: TestClient, db_session: Session):
    """Test 9: Recording consumption against non-existent execution returns 404."""
    user = create_test_user(db_session, "invalid_ex")
    headers = auth_headers(user)
    fake_id = str(uuid.uuid4())
    payload = {
        "material_type": "METAL",
        "material_name": "Gold",
        "actual_quantity": 5.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{fake_id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "EXECUTION_NOT_FOUND"


def test_10_pending_execution_rejected(client: TestClient, db_session: Session):
    """Test 10: Recording consumption against PENDING execution is rejected with 400."""
    user = create_test_user(db_session, "pending_ex")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user, num_steps=2)
    step2_pending = executions[1]
    assert step2_pending.status == "pending"

    headers = auth_headers(user)
    payload = {
        "material_type": "METAL",
        "material_name": "Gold",
        "actual_quantity": 5.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{step2_pending.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_EXECUTION_STATE"


def test_11_ready_execution_rejected(client: TestClient, db_session: Session):
    """Test 11: Recording consumption against READY execution is rejected with 400."""
    user = create_test_user(db_session, "ready_ex")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    step1_ready = executions[0]
    assert step1_ready.status == "ready"

    headers = auth_headers(user)
    payload = {
        "material_type": "METAL",
        "material_name": "Gold",
        "actual_quantity": 5.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{step1_ready.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_EXECUTION_STATE"


def test_12_valid_in_progress_execution_accepted(client: TestClient, db_session: Session):
    """Test 12: Recording consumption against IN_PROGRESS execution succeeds."""
    user = create_test_user(db_session, "inp_accept")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json={"material_type": "METAL", "material_name": "Silver", "actual_quantity": 12.0},
    )
    assert resp.status_code == 201


def test_13_valid_completed_execution_accepted(client: TestClient, db_session: Session):
    """Test 13: Recording post-step final reconciliation consumption against COMPLETED execution succeeds."""
    user = create_test_user(db_session, "comp_accept")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    headers = auth_headers(user)
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json={
            "material_type": "METAL",
            "material_name": "18K Gold",
            "actual_quantity": 8.6,
            "wastage_quantity": 0.2,
            "notes": "Final reconciliation sweep",
        },
    )
    assert resp.status_code == 201


# ==============================================================================
# 3. Specification Linkage
# ==============================================================================

def test_14_valid_specification_material_accepted(client: TestClient, db_session: Session):
    """Test 14: Valid specification material reference is accepted and auto-populates defaults."""
    user = create_test_user(db_session, "spec_mat_ok")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user, metal_weight=8.5)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "specification_material_id": str(mat.id),
        "actual_quantity": 8.7,
        "wastage_quantity": 0.2,
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["specification_material_id"] == str(mat.id)
    assert data["material_type"] == "METAL"
    assert "18k" in data["material_name"].lower()
    assert data["planned_quantity"] == 8.5
    assert data["unit"] == "g"


def test_15_mismatched_specification_material_rejected(client: TestClient, db_session: Session):
    """Test 15: Specification material belonging to a different order's specification is rejected (400)."""
    user = create_test_user(db_session, "spec_mat_mismatch")
    order_a, executions_a, mat_a, gem_a, spec_a = setup_order_with_spec(db_session, user)
    order_b, executions_b, mat_b, gem_b, spec_b = setup_order_with_spec(db_session, user)
    ex_a = executions_a[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex_a.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    # Attempt to link mat_b into ex_a
    payload = {
        "specification_material_id": str(mat_b.id),
        "actual_quantity": 5.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex_a.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SPECIFICATION_MATERIAL_MISMATCH"


def test_16_valid_gemstone_accepted(client: TestClient, db_session: Session):
    """Test 16: Valid specification gemstone reference is accepted and auto-populates defaults."""
    user = create_test_user(db_session, "spec_gem_ok")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user, stone_count=2)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "specification_gemstone_id": str(gem.id),
        "actual_quantity": 2.0,
        "wastage_quantity": 0.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["specification_gemstone_id"] == str(gem.id)
    assert data["material_type"] == "GEMSTONE"
    assert "diamond" in data["material_name"].lower()
    assert data["planned_quantity"] == 2.0


def test_17_mismatched_gemstone_rejected(client: TestClient, db_session: Session):
    """Test 17: Gemstone from another specification is rejected with 400."""
    user = create_test_user(db_session, "spec_gem_mismatch")
    order_a, executions_a, mat_a, gem_a, spec_a = setup_order_with_spec(db_session, user)
    order_b, executions_b, mat_b, gem_b, spec_b = setup_order_with_spec(db_session, user)
    ex_a = executions_a[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex_a.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    payload = {
        "specification_gemstone_id": str(gem_b.id),
        "actual_quantity": 1.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex_a.id}/material-consumption",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SPECIFICATION_GEMSTONE_MISMATCH"


# ==============================================================================
# 4. Tenant Isolation
# ==============================================================================

def test_18_cross_tenant_execution_rejected(client: TestClient, db_session: Session):
    """Test 18: Tenant A cannot record material consumption against Tenant B execution (404)."""
    user_a = create_test_user(db_session, "tenant_a")
    user_b = create_test_user(db_session, "tenant_b")

    _, executions_b, _, _, _ = setup_order_with_spec(db_session, user_b)
    ex_b = executions_b[0]
    production_execution_service.transition_execution(
        db_session, user_b.id, ex_b.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers_a = auth_headers(user_a)
    payload = {
        "material_type": "METAL",
        "material_name": "Gold",
        "actual_quantity": 5.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex_b.id}/material-consumption",
        headers=headers_a,
        json=payload,
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "EXECUTION_NOT_FOUND"


def test_19_cross_tenant_material_rejected(client: TestClient, db_session: Session):
    """Test 19: Tenant A cannot link Tenant B's specification material (404)."""
    user_a = create_test_user(db_session, "tenant_mat_a")
    user_b = create_test_user(db_session, "tenant_mat_b")

    order_a, executions_a, mat_a, _, _ = setup_order_with_spec(db_session, user_a)
    order_b, executions_b, mat_b, _, _ = setup_order_with_spec(db_session, user_b)
    ex_a = executions_a[0]
    production_execution_service.transition_execution(
        db_session, user_a.id, ex_a.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers_a = auth_headers(user_a)
    payload = {
        "specification_material_id": str(mat_b.id),
        "actual_quantity": 5.0,
    }
    resp = client.post(
        f"/api/v1/production/executions/{ex_a.id}/material-consumption",
        headers=headers_a,
        json=payload,
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "SPECIFICATION_MATERIAL_NOT_FOUND"


def test_20_cross_tenant_order_read_rejected(client: TestClient, db_session: Session):
    """Test 20: Tenant A cannot list Tenant B order's consumptions or summary (404)."""
    user_a = create_test_user(db_session, "tenant_read_a")
    user_b = create_test_user(db_session, "tenant_read_b")

    order_b, executions_b, _, _, _ = setup_order_with_spec(db_session, user_b)
    headers_a = auth_headers(user_a)

    resp_list = client.get(
        f"/api/v1/production/orders/{order_b.id}/material-consumption",
        headers=headers_a,
    )
    assert resp_list.status_code == 404
    assert resp_list.json()["error"]["code"] == "ORDER_NOT_FOUND"

    resp_summary = client.get(
        f"/api/v1/production/orders/{order_b.id}/material-summary",
        headers=headers_a,
    )
    assert resp_summary.status_code == 404
    assert resp_summary.json()["error"]["code"] == "ORDER_NOT_FOUND"


# ==============================================================================
# 5. Traceability & Immutability
# ==============================================================================

def test_21_consumption_linked_to_correct_order(db_session: Session):
    """Test 21: Consumption record is persisted with matching production_order_id."""
    user = create_test_user(db_session, "trace_order")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    consumption = production_execution_service.record_material_consumption(
        db_session, user.id, ex.id,
        MaterialConsumptionCreate(
            material_type="METAL",
            material_name="18K Yellow Gold",
            actual_quantity=7.5,
        ),
    )
    assert consumption.production_order_id == order.id


def test_22_consumption_linked_to_correct_execution(db_session: Session):
    """Test 22: Consumption record is persisted with matching operation_execution_id."""
    user = create_test_user(db_session, "trace_exec")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    consumption = production_execution_service.record_material_consumption(
        db_session, user.id, ex.id,
        MaterialConsumptionCreate(
            material_type="METAL",
            material_name="18K Yellow Gold",
            actual_quantity=7.5,
        ),
    )
    assert consumption.operation_execution_id == ex.id


def test_23_specification_planned_value_remains_unchanged(db_session: Session):
    """Test 23: Authoritative ProductionSpecification baseline remains completely unchanged."""
    user = create_test_user(db_session, "spec_immutable")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user, metal_weight=8.50)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    # Record actual consumption with higher weight and wastage
    production_execution_service.record_material_consumption(
        db_session, user.id, ex.id,
        MaterialConsumptionCreate(
            specification_material_id=mat.id,
            actual_quantity=9.20,
            wastage_quantity=0.70,
        ),
    )

    db_session.refresh(spec)
    db_session.refresh(mat)

    # Specification baseline MUST remain 8.50g
    assert mat.estimated_weight_grams == 8.50
    assert spec.estimated_finished_metal_weight_grams == 8.50


def test_24_actual_value_stored_correctly(db_session: Session):
    """Test 24: Actual consumed quantity stored accurately with unit."""
    user = create_test_user(db_session, "actual_val")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    consumption = production_execution_service.record_material_consumption(
        db_session, user.id, ex.id,
        MaterialConsumptionCreate(
            material_type="METAL",
            material_name="Sterling Silver 925",
            unit="g",
            actual_quantity=15.425,
            wastage_quantity=0.125,
        ),
    )
    assert consumption.actual_quantity == 15.425
    assert consumption.unit == "g"


def test_25_wastage_stored_correctly(db_session: Session):
    """Test 25: Wastage quantity and reason stored accurately."""
    user = create_test_user(db_session, "wastage_val")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    consumption = production_execution_service.record_material_consumption(
        db_session, user.id, ex.id,
        MaterialConsumptionCreate(
            material_type="GEMSTONE",
            material_name="Ruby (Oval 6x4)",
            unit="pcs",
            actual_quantity=1.0,
            wastage_quantity=1.0,
            wastage_reason="Girdle fractured under setting hammer pressure",
        ),
    )
    assert consumption.wastage_quantity == 1.0
    assert "fractured" in consumption.wastage_reason


# ==============================================================================
# 6. Summary Tests
# ==============================================================================

def test_26_order_summary_returns_planned_actual_wastage(client: TestClient, db_session: Session):
    """Test 26: Order summary endpoint returns planned, actual, and wastage quantities."""
    user = create_test_user(db_session, "summary_check")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json={
            "material_type": "METAL",
            "material_name": "18K Gold",
            "unit": "g",
            "planned_quantity": 8.50,
            "actual_quantity": 8.80,
            "wastage_quantity": 0.30,
        },
    )

    resp = client.get(
        f"/api/v1/production/orders/{order.id}/material-summary",
        headers=headers,
    )
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["order_id"] == str(order.id)
    assert summary["total_planned_quantity"] == 8.50
    assert summary["total_actual_quantity"] == 8.80
    assert summary["total_wastage_quantity"] == 0.30
    assert summary["total_net_quantity"] == 8.50
    assert len(summary["items"]) == 1
    assert summary["items"][0]["material_name"] == "18K Gold"


def test_27_multiple_consumption_records_aggregate_correctly(client: TestClient, db_session: Session):
    """Test 27: Multiple draws across operations aggregate correctly by material in order summary."""
    user = create_test_user(db_session, "summary_agg")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user, num_steps=2)
    ex1 = executions[0]
    ex2 = executions[1]

    # Advance ex1 through IN_PROGRESS and COMPLETED
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    headers = auth_headers(user)

    # Step 1: Draw 1 for 18K Gold
    client.post(
        f"/api/v1/production/executions/{ex1.id}/material-consumption",
        headers=headers,
        json={
            "material_type": "METAL",
            "material_name": "18K Gold",
            "unit": "g",
            "planned_quantity": 8.50,
            "actual_quantity": 5.00,
            "wastage_quantity": 0.20,
        },
    )
    # Step 1: Gemstone draw
    client.post(
        f"/api/v1/production/executions/{ex1.id}/material-consumption",
        headers=headers,
        json={
            "material_type": "GEMSTONE",
            "material_name": "Round Diamond",
            "unit": "pcs",
            "planned_quantity": 1.0,
            "actual_quantity": 1.0,
            "wastage_quantity": 0.0,
        },
    )

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    # Step 2: Transition to IN_PROGRESS and draw additional 18K Gold (e.g. sizing solder)
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    client.post(
        f"/api/v1/production/executions/{ex2.id}/material-consumption",
        headers=headers,
        json={
            "material_type": "METAL",
            "material_name": "18K Gold",
            "unit": "g",
            "planned_quantity": 0.0,
            "actual_quantity": 3.80,
            "wastage_quantity": 0.10,
        },
    )

    resp = client.get(
        f"/api/v1/production/orders/{order.id}/material-summary",
        headers=headers,
    )
    assert resp.status_code == 200
    summary = resp.json()

    gold_items = [i for i in summary["items"] if i["material_name"] == "18K Gold"]
    assert len(gold_items) == 1
    gold = gold_items[0]
    # 5.00 + 3.80 = 8.80
    assert gold["actual_quantity"] == 8.80
    # 0.20 + 0.10 = 0.30
    assert gold["wastage_quantity"] == 0.30
    # 8.80 - 0.30 = 8.50 net
    assert gold["net_consumed_quantity"] == 8.50

    diamond_items = [i for i in summary["items"] if i["material_name"] == "Round Diamond"]
    assert len(diamond_items) == 1
    assert diamond_items[0]["actual_quantity"] == 1.0


# ==============================================================================
# 7. Additional Robustness & Security Tests
# ==============================================================================

def test_28_client_field_injection_forbidden(client: TestClient, db_session: Session):
    """Test 28: Client cannot inject user_id, production_order_id, or execution_id in payload."""
    user = create_test_user(db_session, "inject_fields")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    # Attempt to inject user_id
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json={
            "material_type": "METAL",
            "material_name": "Gold",
            "actual_quantity": 5.0,
            "user_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 422

    # Attempt to inject production_order_id
    resp2 = client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json={
            "material_type": "METAL",
            "material_name": "Gold",
            "actual_quantity": 5.0,
            "production_order_id": str(uuid.uuid4()),
        },
    )
    assert resp2.status_code == 422


def test_29_list_execution_material_consumptions_endpoint(client: TestClient, db_session: Session):
    """Test 29: GET /executions/{id}/material-consumption lists records for that execution."""
    user = create_test_user(db_session, "list_exec")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json={"material_type": "METAL", "material_name": "Gold A", "actual_quantity": 2.0},
    )
    client.post(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
        json={"material_type": "METAL", "material_name": "Gold B", "actual_quantity": 3.0},
    )

    resp = client.get(
        f"/api/v1/production/executions/{ex.id}/material-consumption",
        headers=headers,
    )
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 2
    assert records[0]["material_name"] == "Gold A"
    assert records[1]["material_name"] == "Gold B"


def test_30_list_order_material_consumptions_endpoint(client: TestClient, db_session: Session):
    """Test 30: GET /orders/{id}/material-consumption lists all records across order steps."""
    user = create_test_user(db_session, "list_order")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user, num_steps=2)
    ex1, ex2 = executions[0], executions[1]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    headers = auth_headers(user)
    client.post(
        f"/api/v1/production/executions/{ex1.id}/material-consumption",
        headers=headers,
        json={"material_type": "METAL", "material_name": "Gold Step 1", "actual_quantity": 4.0},
    )
    client.post(
        f"/api/v1/production/executions/{ex2.id}/material-consumption",
        headers=headers,
        json={"material_type": "GEMSTONE", "material_name": "Diamond Step 2", "actual_quantity": 1.0},
    )

    resp = client.get(
        f"/api/v1/production/orders/{order.id}/material-consumption",
        headers=headers,
    )
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 2


def test_31_append_only_auditability(db_session: Session):
    """Test 31: Subsequent material recordings are append-only and do not mutate previous records."""
    user = create_test_user(db_session, "audit_append")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    c1 = production_execution_service.record_material_consumption(
        db_session, user.id, ex.id,
        MaterialConsumptionCreate(
            material_type="METAL",
            material_name="18K Yellow Gold",
            actual_quantity=5.0,
            wastage_quantity=0.1,
            notes="Draw 1",
        ),
    )
    c1_id = c1.id

    c2 = production_execution_service.record_material_consumption(
        db_session, user.id, ex.id,
        MaterialConsumptionCreate(
            material_type="METAL",
            material_name="18K Yellow Gold",
            actual_quantity=3.5,
            wastage_quantity=0.2,
            notes="Draw 2",
        ),
    )

    db_session.refresh(c1)
    # c1 remains unchanged
    assert c1.id == c1_id
    assert c1.actual_quantity == 5.0
    assert c1.wastage_quantity == 0.1
    assert c1.notes == "Draw 1"
    # c2 is a distinct record
    assert c2.id != c1_id
    assert c2.actual_quantity == 3.5


def test_32_execution_state_machine_unaffected(db_session: Session):
    """Test 32: Recording material consumption does not alter execution status or order status."""
    user = create_test_user(db_session, "statemachine_unaffected")
    order, executions, mat, gem, spec = setup_order_with_spec(db_session, user)
    ex = executions[0]
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    # Record material
    production_execution_service.record_material_consumption(
        db_session, user.id, ex.id,
        MaterialConsumptionCreate(
            material_type="METAL",
            material_name="Gold",
            actual_quantity=8.0,
        ),
    )

    db_session.refresh(ex)
    db_session.refresh(order)

    # Status must strictly remain IN_PROGRESS
    assert ex.status == ExecutionStatus.IN_PROGRESS.value
    # Order status unaffected
    assert order.status == "in_progress"
