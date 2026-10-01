"""
Phase J.5 — Quality Control & Controlled Rework Test Suite
Comprehensive testing for:
1. QC creation (PASS, FAIL, REWORK)
2. QC validation & error handling
3. Execution state enforcement (only COMPLETED allowed)
4. Multi-tenant isolation & IDOR prevention
5. Client-controlled audit injection forbidden (extra="forbid")
6. Append-only QC history preservation
7. Latest QC outcome determination
8. Production order completion gating (all PASS vs missing/fail/rework)
9. Controlled rework execution lifecycle & attempt numbering
10. Original execution immutability
11. Rework worker/machine assignment (J.3)
12. Rework material consumption & wastage tracking (J.4)
13. Rework resolution loop to order completion
14. Order quality summary metrics accuracy
"""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token
from app.models.design import Design, DesignRender
from app.models.execution import MaterialConsumption, OperationExecution, QualityCheck
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
    DefectSeverity,
    ExecutionStatus,
    MaterialConsumptionCreate,
    OperationExecutionTransitionRequest,
    QualityCheckCreate,
    QualityCheckResult,
    ReworkExecutionCreate,
)
from app.services.production_execution_service import production_execution_service
from app.services.user_service import user_service


# ==============================================================================
# Fixtures and Environment Setup Helpers
# ==============================================================================

def create_test_user(db: Session, email_prefix: str = "j5_artisan") -> User:
    """Creates a unique test user in the database."""
    unique_email = f"{email_prefix}.{uuid.uuid4().hex[:8]}@jewelmind.atelier"
    return user_service.create(
        db,
        UserCreate(
            email=unique_email,
            password="SecurePassword123!",
            full_name=f"Master QC Inspector {email_prefix.title()}",
        ),
    )


def auth_headers(user: User) -> dict:
    """Generates bearer authorization headers for a user."""
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def setup_j5_order_environment(
    db: Session,
    user: User,
    num_steps: int = 2,
) -> tuple[ProductionOrder, list[OperationExecution], ProductionSpecification]:
    """
    Sets up a complete production order environment with N routing steps
    and initialized operation executions.
    """
    # 1. Design & Render
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Handmade Diamond Halo Pendant",
        category="pendant",
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
        prompt="18k white gold diamond halo pendant",
        image_url="https://storage.jewelmind.internal/renders/pendant_j5.png",
        is_approved_for_production=True,
    )
    db.add(render)
    db.commit()

    # 2. Specification
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        category="pendant",
        estimated_rough_metal_weight_grams=12.0,
        estimated_finished_metal_weight_grams=10.5,
        total_gemstone_count=12,
        estimated_total_bench_hours=6.0,
        complexity_rating="intricate",
        approved_at=datetime.now(timezone.utc),
    )
    db.add(spec)
    db.commit()

    # 3. Materials
    mat = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type="White Gold",
        metal_purity="18K",
        metal_color="White",
        estimated_weight_grams=12.0,
    )
    db.add(mat)

    gem = ProductionGemstone(
        id=uuid.uuid4(),
        specification_id=spec.id,
        gemstone_type="Diamond",
        cut_shape="Round Brilliant",
        stone_count=12,
        estimated_carat_weight=1.20,
    )
    db.add(gem)
    db.commit()

    # 4. Steps
    stage_data = [
        ("Precision Casting", "casting", "casting_furnace"),
        ("Micro-Prong Stone Setting", "stone_setting", "bench_microscope"),
        ("Final Polish & Ultrasonic", "polishing", "ultrasonic_cleaner"),
    ]
    for i in range(num_steps):
        s_data = stage_data[i % len(stage_data)]
        step = ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=i + 1,
            stage_name=s_data[0],
            required_skill=s_data[1],
            required_machine_type=s_data[2],
            base_hours=2.0,
            per_unit_hours=0.5,
            quality_checkpoint=f"Inspection checkpoint for {s_data[0]}",
        )
        db.add(step)
    db.commit()

    # 5. Production Order
    order = ProductionOrder(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        quantity=1,
        priority="high",
        status="pending",
        deadline=datetime.now(timezone.utc) + timedelta(days=10),
        specification_id=spec.id,
    )
    db.add(order)
    db.commit()

    # 6. Initialize executions
    executions = production_execution_service.initialize_order_executions(
        db=db,
        user_id=user.id,
        order_id=order.id,
    )

    return order, executions, spec


# ==============================================================================
# A. Quality Check Creation Tests (PASS, FAIL, REWORK)
# ==============================================================================

def test_j5_01_qc_pass_on_completed_execution(client: TestClient, db_session: Session):
    """Test 1: Record PASS quality check on completed operation execution (HTTP 201)."""
    user = create_test_user(db_session, "qc_pass")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1 = executions[0]

    # Advance to COMPLETED
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    payload = {
        "result": "PASS",
        "defect_severity": "NONE",
        "notes": "Prongs aligned perfectly, stone seated securely.",
        "checked_by": "INSP-402",
    }
    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json=payload,
        headers=auth_headers(user),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["result"] == "PASS"
    assert data["defect_severity"] == "NONE"
    assert data["checked_by"] == "INSP-402"
    assert data["operation_execution_id"] == str(ex1.id)
    assert data["production_order_id"] == str(order.id)
    assert data["production_step_id"] == str(ex1.production_step_id)


def test_j5_02_qc_fail_on_completed_execution(client: TestClient, db_session: Session):
    """Test 2: Record FAIL quality check on completed execution with defect details (HTTP 201)."""
    user = create_test_user(db_session, "qc_fail")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1 = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    payload = {
        "result": "FAIL",
        "defect_severity": "CRITICAL",
        "defect_type": "POROSITY_VOID",
        "notes": "Severe sub-surface metal void detected during density testing.",
        "checked_by": "INSP-991",
    }
    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json=payload,
        headers=auth_headers(user),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["result"] == "FAIL"
    assert data["defect_severity"] == "CRITICAL"
    assert data["defect_type"] == "POROSITY_VOID"


def test_j5_03_qc_rework_on_completed_execution(client: TestClient, db_session: Session):
    """Test 3: Record REWORK quality check on completed execution (HTTP 201)."""
    user = create_test_user(db_session, "qc_rework")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1 = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    payload = {
        "result": "REWORK",
        "defect_severity": "MEDIUM",
        "defect_type": "SURFACE_SCRATCH",
        "notes": "Fine abrasive scratch near north bezel. Requires re-buffing.",
        "checked_by": "INSP-104",
    }
    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json=payload,
        headers=auth_headers(user),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["result"] == "REWORK"
    assert data["defect_severity"] == "MEDIUM"


# ==============================================================================
# B. Execution State Enforcement Tests
# ==============================================================================

def test_j5_04_qc_rejected_on_ready_execution(client: TestClient, db_session: Session):
    """Test 4: QC check is rejected on READY execution (HTTP 409)."""
    user = create_test_user(db_session, "qc_ready_fail")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1 = executions[0]
    assert ex1.status == "ready"

    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json={"result": "PASS"},
        headers=auth_headers(user),
    )
    assert res.status_code == 409
    err_msg = res.json().get("error", {}).get("message") or res.json().get("detail", "")
    assert "COMPLETED operations" in err_msg


def test_j5_05_qc_rejected_on_in_progress_execution(client: TestClient, db_session: Session):
    """Test 5: QC check is rejected on IN_PROGRESS execution (HTTP 409)."""
    user = create_test_user(db_session, "qc_inprogress_fail")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1 = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json={"result": "PASS"},
        headers=auth_headers(user),
    )
    assert res.status_code == 409


def test_j5_06_qc_rejected_on_pending_execution(client: TestClient, db_session: Session):
    """Test 6: QC check is rejected on PENDING execution (HTTP 409)."""
    user = create_test_user(db_session, "qc_pending_fail")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex2 = executions[1]
    assert ex2.status == "pending"

    res = client.post(
        f"/api/v1/production/executions/{ex2.id}/quality-check",
        json={"result": "PASS"},
        headers=auth_headers(user),
    )
    assert res.status_code == 409


def test_j5_07_qc_rejected_on_paused_execution(client: TestClient, db_session: Session):
    """Test 7: QC check is rejected on PAUSED execution (HTTP 409)."""
    user = create_test_user(db_session, "qc_paused_fail")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1 = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.PAUSED),
    )
    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json={"result": "PASS"},
        headers=auth_headers(user),
    )
    assert res.status_code == 409


# ==============================================================================
# C. Validation & Schema Enforcement Tests
# ==============================================================================

def test_j5_08_invalid_qc_result_rejected(client: TestClient, db_session: Session):
    """Test 8: Invalid QC result string is rejected with HTTP 422."""
    user = create_test_user(db_session, "qc_invalid_res")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json={"result": "MAYBE"},
        headers=auth_headers(user),
    )
    assert res.status_code == 422


def test_j5_09_invalid_defect_severity_rejected(client: TestClient, db_session: Session):
    """Test 9: Invalid defect severity string is rejected with HTTP 422."""
    user = create_test_user(db_session, "qc_invalid_sev")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json={"result": "FAIL", "defect_severity": "SUPER_CRITICAL"},
        headers=auth_headers(user),
    )
    assert res.status_code == 422


def test_j5_10_pass_with_critical_defect_rejected(client: TestClient, db_session: Session):
    """Test 10: PASS result with CRITICAL defect severity is rejected by Pydantic validator (HTTP 422)."""
    user = create_test_user(db_session, "qc_pass_crit")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json={"result": "PASS", "defect_severity": "CRITICAL"},
        headers=auth_headers(user),
    )
    assert res.status_code == 422


def test_j5_11_qc_non_existent_execution_rejected(client: TestClient, db_session: Session):
    """Test 11: Non-existent execution ID returns HTTP 404."""
    user = create_test_user(db_session, "qc_nonexistent")
    fake_id = uuid.uuid4()

    res = client.post(
        f"/api/v1/production/executions/{fake_id}/quality-check",
        json={"result": "PASS"},
        headers=auth_headers(user),
    )
    assert res.status_code == 404


def test_j5_12_client_field_injection_forbidden(client: TestClient, db_session: Session):
    """Test 12: Client cannot supply user_id, production_order_id, or checked_at (extra='forbid', HTTP 422)."""
    user = create_test_user(db_session, "qc_injection")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json={
            "result": "PASS",
            "user_id": str(uuid.uuid4()),  # Forbidden
            "checked_at": "2026-01-01T00:00:00Z",  # Forbidden
        },
        headers=auth_headers(user),
    )
    assert res.status_code == 422


# ==============================================================================
# D. Multi-Tenant Security Tests
# ==============================================================================

def test_j5_13_cross_tenant_qc_creation_rejected(client: TestClient, db_session: Session):
    """Test 13: User B cannot record QC on User A's execution (HTTP 404)."""
    user_a = create_test_user(db_session, "tenant_a")
    user_b = create_test_user(db_session, "tenant_b")
    order_a, executions_a, _ = setup_j5_order_environment(db_session, user_a, num_steps=1)
    ex_a = executions_a[0]

    # User A completes operation
    production_execution_service.transition_execution(
        db_session, user_a.id, ex_a.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user_a.id, ex_a.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    # User B attempts to record QC
    res = client.post(
        f"/api/v1/production/executions/{ex_a.id}/quality-check",
        json={"result": "PASS"},
        headers=auth_headers(user_b),
    )
    assert res.status_code == 404


def test_j5_14_cross_tenant_execution_qc_history_rejected(client: TestClient, db_session: Session):
    """Test 14: User B cannot view QC history for User A's execution (HTTP 404)."""
    user_a = create_test_user(db_session, "tenant_a_hist")
    user_b = create_test_user(db_session, "tenant_b_hist")
    order_a, executions_a, _ = setup_j5_order_environment(db_session, user_a, num_steps=1)
    ex_a = executions_a[0]

    res = client.get(
        f"/api/v1/production/executions/{ex_a.id}/quality-check",
        headers=auth_headers(user_b),
    )
    assert res.status_code == 404


def test_j5_15_cross_tenant_order_qc_summary_rejected(client: TestClient, db_session: Session):
    """Test 15: User B cannot view QC summary for User A's order (HTTP 404)."""
    user_a = create_test_user(db_session, "tenant_a_sum")
    user_b = create_test_user(db_session, "tenant_b_sum")
    order_a, _, _ = setup_j5_order_environment(db_session, user_a, num_steps=1)

    res = client.get(
        f"/api/v1/production/orders/{order_a.id}/quality-checks",
        headers=auth_headers(user_b),
    )
    assert res.status_code == 404


# ==============================================================================
# E. QC History & Latest Outcome Determination Tests
# ==============================================================================

def test_j5_16_append_only_qc_history_preserved(client: TestClient, db_session: Session):
    """Test 16: Multiple QC checks are preserved append-only, ordered newest first."""
    user = create_test_user(db_session, "qc_history")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    # First check: FAIL
    client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json={"result": "FAIL", "defect_severity": "HIGH", "notes": "First inspection failed."},
        headers=auth_headers(user),
    )
    # Second check: PASS (after supervisor review/adjustment)
    client.post(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        json={"result": "PASS", "defect_severity": "NONE", "notes": "Re-inspected under high power: acceptable tolerance."},
        headers=auth_headers(user),
    )

    res = client.get(
        f"/api/v1/production/executions/{ex1.id}/quality-check",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 2
    # Latest first
    assert history[0]["result"] == "PASS"
    assert history[1]["result"] == "FAIL"


def test_j5_17_latest_qc_outcome_determined_accurately(client: TestClient, db_session: Session):
    """Test 17: Operation execution serialization exposes latest QC outcome."""
    user = create_test_user(db_session, "qc_latest")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.PASS, defect_severity=DefectSeverity.NONE),
    )

    res = client.get(
        f"/api/v1/production/executions/{ex1.id}",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["latest_qc_result"] == "PASS"
    assert data["latest_defect_severity"] == "NONE"
    assert data["quality_gate_passed"] is True


# ==============================================================================
# F. Production Order Completion Gating Tests
# ==============================================================================

def test_j5_18_order_completion_gating_missing_qc_blocks_completion(client: TestClient, db_session: Session):
    """Test 18: Step 1 PASS, Step 2 COMPLETED without QC -> Order stays in_progress."""
    user = create_test_user(db_session, "gate_missing_qc")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1, ex2 = executions[0], executions[1]

    # Step 1: Complete and QC PASS
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.PASS),
    )

    # Step 2: Complete but DO NOT record QC
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    db_session.refresh(order)
    # Order must NOT be completed because step 2 has missing QC
    assert order.status == "in_progress"


def test_j5_19_order_completion_gating_fail_blocks_completion(client: TestClient, db_session: Session):
    """Test 19: Step 1 PASS, Step 2 FAIL -> Order stays in_progress."""
    user = create_test_user(db_session, "gate_fail_qc")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1, ex2 = executions[0], executions[1]

    # Step 1: Complete and PASS
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.PASS),
    )

    # Step 2: Complete and FAIL
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex2.id,
        QualityCheckCreate(result=QualityCheckResult.FAIL, defect_severity=DefectSeverity.HIGH),
    )

    db_session.refresh(order)
    assert order.status == "in_progress"


def test_j5_20_order_completion_gating_rework_blocks_completion(client: TestClient, db_session: Session):
    """Test 20: Step 1 PASS, Step 2 REWORK -> Order stays in_progress."""
    user = create_test_user(db_session, "gate_rework_qc")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1, ex2 = executions[0], executions[1]

    # Step 1 PASS
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.PASS),
    )

    # Step 2 REWORK
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex2.id,
        QualityCheckCreate(result=QualityCheckResult.REWORK, defect_severity=DefectSeverity.MEDIUM),
    )

    db_session.refresh(order)
    assert order.status == "in_progress"


def test_j5_21_order_completion_gating_all_pass_completes_order(client: TestClient, db_session: Session):
    """Test 21: Step 1 PASS, Step 2 PASS -> Order transitions to completed."""
    user = create_test_user(db_session, "gate_all_pass")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1, ex2 = executions[0], executions[1]

    # Step 1 PASS
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.PASS),
    )

    # Step 2 PASS
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex2.id,
        QualityCheckCreate(result=QualityCheckResult.PASS),
    )

    db_session.refresh(order)
    assert order.status == "completed"


def test_j5_22_complete_order_endpoint_success(client: TestClient, db_session: Session):
    """Test 22: POST /orders/{order_id}/complete succeeds when quality gate is met."""
    user = create_test_user(db_session, "complete_order_ok")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.PASS),
    )

    res = client.post(
        f"/api/v1/production/orders/{order.id}/complete",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "completed"


def test_j5_23_complete_order_endpoint_blocks_unverified_order(client: TestClient, db_session: Session):
    """Test 23: POST /orders/{order_id}/complete returns 409 if QC gate has not passed."""
    user = create_test_user(db_session, "complete_order_block")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    # Operation completed but NO QC recorded
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    res = client.post(
        f"/api/v1/production/orders/{order.id}/complete",
        headers=auth_headers(user),
    )
    assert res.status_code == 409
    err_msg = res.json().get("error", {}).get("message") or res.json().get("detail", "")
    assert "quality gate has not passed" in err_msg


# ==============================================================================
# G. Controlled Rework Implementation Tests
# ==============================================================================

def test_j5_24_explicit_rework_creation_success(client: TestClient, db_session: Session):
    """Test 24: Create rework execution following REWORK QC outcome (HTTP 201)."""
    user = create_test_user(db_session, "rework_create")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    # Complete and record REWORK
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.REWORK, defect_severity=DefectSeverity.MEDIUM),
    )

    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/rework",
        json={"operator_notes": "Supervisor approved bench rework."},
        headers=auth_headers(user),
    )
    assert res.status_code == 201
    rework = res.json()
    assert rework["execution_type"] == "rework"
    assert rework["attempt_number"] == 2
    assert rework["rework_of_execution_id"] == str(ex1.id)
    assert rework["status"] == "ready"
    assert rework["production_order_id"] == str(order.id)
    assert rework["production_step_id"] == str(ex1.production_step_id)


def test_j5_25_original_execution_immutable_after_rework(client: TestClient, db_session: Session):
    """Test 25: Original execution remains COMPLETED and immutable after rework authorization."""
    user = create_test_user(db_session, "orig_immutable")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED, operator_notes="Initial bench notes"),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.REWORK),
    )

    # Authorize rework
    client.post(
        f"/api/v1/production/executions/{ex1.id}/rework",
        json={"operator_notes": "Authorize rework"},
        headers=auth_headers(user),
    )

    # Refresh original execution
    db_session.refresh(ex1)
    assert ex1.status == "completed"
    assert ex1.execution_type == "normal"
    assert ex1.attempt_number == 1
    assert "Initial bench notes" in (ex1.operator_notes or "")


def test_j5_26_rework_rejected_without_rework_qc(client: TestClient, db_session: Session):
    """Test 26: Rework creation is rejected if latest QC is PASS or not REWORK (HTTP 409)."""
    user = create_test_user(db_session, "rework_no_qc")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    # Check is PASS, not REWORK
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.PASS),
    )

    res = client.post(
        f"/api/v1/production/executions/{ex1.id}/rework",
        json={"operator_notes": "Try rework anyway"},
        headers=auth_headers(user),
    )
    assert res.status_code == 409
    err_msg = res.json().get("error", {}).get("message") or res.json().get("detail", "")
    assert "requires an explicit REWORK quality check" in err_msg


def test_j5_27_duplicate_active_rework_rejected(client: TestClient, db_session: Session):
    """Test 27: Attempting to create duplicate active rework for same step raises HTTP 409."""
    user = create_test_user(db_session, "rework_dup")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.REWORK),
    )

    # First rework: succeeds
    res1 = client.post(
        f"/api/v1/production/executions/{ex1.id}/rework",
        headers=auth_headers(user),
    )
    assert res1.status_code == 201

    # Second rework while attempt #2 is still active: rejected
    res2 = client.post(
        f"/api/v1/production/executions/{ex1.id}/rework",
        headers=auth_headers(user),
    )
    assert res2.status_code == 409
    err_msg = res2.json().get("error", {}).get("message") or res2.json().get("detail", "")
    assert "already exists for this step" in err_msg


def test_j5_28_cross_tenant_rework_creation_rejected(client: TestClient, db_session: Session):
    """Test 28: User B cannot create rework for User A's execution (HTTP 404)."""
    user_a = create_test_user(db_session, "tenant_a_rework")
    user_b = create_test_user(db_session, "tenant_b_rework")
    order_a, executions_a, _ = setup_j5_order_environment(db_session, user_a, num_steps=1)
    ex_a = executions_a[0]

    production_execution_service.transition_execution(
        db_session, user_a.id, ex_a.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user_a.id, ex_a.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user_a.id, ex_a.id,
        QualityCheckCreate(result=QualityCheckResult.REWORK),
    )

    res = client.post(
        f"/api/v1/production/executions/{ex_a.id}/rework",
        headers=auth_headers(user_b),
    )
    assert res.status_code == 404


def test_j5_29_rework_execution_lifecycle_and_worker_assignment(client: TestClient, db_session: Session):
    """Test 29: Rework execution follows J.2/J.3 workflow: assign worker, start, and complete."""
    user = create_test_user(db_session, "rework_lifecycle")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    # Create worker and machine with matching skill & type
    worker = Worker(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Senior Caster Elena",
        skill="casting",
        capacity_hours_per_day=8.0,
        is_available=True,
    )
    db_session.add(worker)

    machine = Machine(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Induction Furnace #1",
        machine_type="casting_furnace",
        capacity_hours_per_day=8.0,
        is_available=True,
    )
    db_session.add(machine)
    db_session.commit()

    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS, validate_resources=False),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.REWORK),
    )

    # 1. Authorize rework
    rework = production_execution_service.create_rework_execution(
        db_session, user.id, ex1.id
    )
    assert rework.status == "ready"

    # 2. Assign worker and machine (J.3)
    assign_w_res = client.post(
        f"/api/v1/production/executions/{rework.id}/assign-worker",
        json={"worker_id": str(worker.id)},
        headers=auth_headers(user),
    )
    assert assign_w_res.status_code == 200
    assert assign_w_res.json()["worker_id"] == str(worker.id)

    assign_m_res = client.post(
        f"/api/v1/production/executions/{rework.id}/assign-machine",
        json={"machine_id": str(machine.id)},
        headers=auth_headers(user),
    )
    assert assign_m_res.status_code == 200
    assert assign_m_res.json()["machine_id"] == str(machine.id)

    # 3. Transition READY -> IN_PROGRESS -> COMPLETED (J.2)
    start_res = client.post(
        f"/api/v1/production/executions/{rework.id}/transition",
        json={"target_status": "in_progress"},
        headers=auth_headers(user),
    )
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "in_progress"

    finish_res = client.post(
        f"/api/v1/production/executions/{rework.id}/transition",
        json={"target_status": "completed", "operator_notes": "Rework cast flawless."},
        headers=auth_headers(user),
    )
    assert finish_res.status_code == 200
    assert finish_res.json()["status"] == "completed"


# ==============================================================================
# H. Rework Material Consumption Integration Tests (J.4)
# ==============================================================================

def test_j5_30_rework_material_consumption_integration(client: TestClient, db_session: Session):
    """Test 30: Rework execution records separate traceable MaterialConsumption (J.4)."""
    user = create_test_user(db_session, "rework_mat")
    order, executions, spec = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    # Start initial execution (IN_PROGRESS)
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS, validate_resources=False),
    )

    # Draw material on initial execution
    mat_payload1 = {
        "material_type": "METAL",
        "material_name": "18K White Gold",
        "unit": "g",
        "planned_quantity": 12.0,
        "actual_quantity": 12.5,
        "wastage_quantity": 0.5,
    }
    res_mat1 = client.post(
        f"/api/v1/production/executions/{ex1.id}/material-consumption",
        json=mat_payload1,
        headers=auth_headers(user),
    )
    assert res_mat1.status_code == 201

    # Complete initial execution & QC REWORK
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.REWORK),
    )

    # Authorize rework execution
    rework = production_execution_service.create_rework_execution(
        db_session, user.id, ex1.id
    )

    # Start rework execution so it is IN_PROGRESS (J.4 requirement)
    production_execution_service.transition_execution(
        db_session, user.id, rework.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS, validate_resources=False),
    )

    # Draw additional material on rework execution
    mat_payload2 = {
        "material_type": "METAL",
        "material_name": "18K White Gold Rework Feedstock",
        "unit": "g",
        "planned_quantity": 2.0,
        "actual_quantity": 2.2,
        "wastage_quantity": 0.2,
        "wastage_reason": "Sprue trimmings on second casting attempt",
    }
    res_mat2 = client.post(
        f"/api/v1/production/executions/{rework.id}/material-consumption",
        json=mat_payload2,
        headers=auth_headers(user),
    )
    assert res_mat2.status_code == 201

    # Verify order material summary aggregates both cleanly
    summary_res = client.get(
        f"/api/v1/production/orders/{order.id}/material-summary",
        headers=auth_headers(user),
    )
    assert summary_res.status_code == 200
    s_data = summary_res.json()
    assert s_data["total_actual_quantity"] == round(12.5 + 2.2, 4)
    assert s_data["total_wastage_quantity"] == round(0.5 + 0.2, 4)


# ==============================================================================
# I. Complete Rework Resolution Loop & Order Quality Summary Tests
# ==============================================================================

def test_j5_31_rework_loop_second_attempt_pass_completes_order(client: TestClient, db_session: Session):
    """Test 31: Full loop: initial REWORK -> rework attempt -> PASS -> order COMPLETED."""
    user = create_test_user(db_session, "full_loop")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=1)
    ex1 = executions[0]

    # Initial execution -> COMPLETED -> REWORK
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.REWORK, defect_severity=DefectSeverity.LOW),
    )
    db_session.refresh(order)
    assert order.status == "in_progress"

    # Create rework execution
    rework = production_execution_service.create_rework_execution(
        db_session, user.id, ex1.id
    )

    # Execute rework: READY -> IN_PROGRESS -> COMPLETED
    production_execution_service.transition_execution(
        db_session, user.id, rework.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, rework.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    # QC inspection on rework: PASS
    qc_res = client.post(
        f"/api/v1/production/executions/{rework.id}/quality-check",
        json={"result": "PASS", "defect_severity": "NONE", "notes": "Rework piece passes all tolerances."},
        headers=auth_headers(user),
    )
    assert qc_res.status_code == 201

    # Order must now be completed!
    db_session.refresh(order)
    assert order.status == "completed"


def test_j5_32_order_qc_summary_endpoint_accuracy(client: TestClient, db_session: Session):
    """Test 32: GET /orders/{order_id}/quality-checks returns accurate structured metrics."""
    user = create_test_user(db_session, "qc_summary_acc")
    order, executions, _ = setup_j5_order_environment(db_session, user, num_steps=2)
    ex1, ex2 = executions[0], executions[1]

    # Complete Step 1 -> PASS
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex1.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex1.id,
        QualityCheckCreate(result=QualityCheckResult.PASS),
    )

    # Complete Step 2 -> REWORK
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex2.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    production_execution_service.record_quality_check(
        db_session, user.id, ex2.id,
        QualityCheckCreate(result=QualityCheckResult.REWORK, defect_severity=DefectSeverity.MEDIUM),
    )

    res = client.get(
        f"/api/v1/production/orders/{order.id}/quality-checks",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    summary = res.json()
    assert summary["order_id"] == str(order.id)
    assert summary["total_operations"] == 2
    assert summary["completed_operations"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 0
    assert summary["rework"] == 1
    assert summary["pending_quality_checks"] == 0
    assert summary["quality_gate_passed"] is False
    assert len(summary["items"]) == 2
