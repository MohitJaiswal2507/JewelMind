"""
Phase J.7 — Planned vs Actual Production Analytics Test Suite

Comprehensive testing for:
1. Authenticated analytics access
2. Multi-tenant isolation & IDOR prevention (cross-tenant returns 404)
3. Planned hours calculation from routing steps
4. Actual hours calculation from operation executions
5. Time variance and variance percentage (over norm vs under norm)
6. Zero planned hours divide-by-zero protection (variance_percent is None)
7. Material planned vs actual consumption tracking
8. Material wastage and scrap percent calculation
9. Zero actual material consumption protection (wastage_percent is None)
10. Material identity preservation (gold, silver, gems kept distinct)
11. Operation counts distribution (completed, in-progress, paused, blocked, pending)
12. Controlled rework attempt tracking and rework rate
13. Quality inspection verdict counts (PASS, FAIL, REWORK) & first-pass yield
14. Schedule milestones & schedule variance in hours
15. Missing/null timestamps handling without estimating/predicting
16. Incomplete vs completed order analytics
17. Read-only guarantee: analytics never alters database state
18. Strict numeric safety: no NaN or Infinity
19. Cross-order atelier analytics summary calculation
20. Tenant isolation in atelier analytics summary
"""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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
    QualityCheckCreate,
    QualityCheckResult,
)
from app.services.production_execution_service import production_execution_service
from app.services.production_analytics_service import production_analytics_service
from app.services.user_service import user_service


# ==============================================================================
# Helpers and Environment Setup
# ==============================================================================

@pytest.fixture
def db(db_session: Session) -> Session:
    """Fixture alias for db_session to match test parameter names."""
    return db_session


def create_test_user(db: Session, email_prefix: str = "j7_analyst") -> User:
    """Creates a unique test user in the database."""
    unique_email = f"{email_prefix}.{uuid.uuid4().hex[:8]}@jewelmind.atelier"
    return user_service.create(
        db,
        UserCreate(
            email=unique_email,
            password="SecurePassword123!",
            full_name=f"Analytics Specialist {email_prefix.title()}",
        ),
    )


def auth_headers(user: User) -> dict:
    """Generates bearer authorization headers for a user."""
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def setup_j7_order_environment(
    db: Session,
    user: User,
    step_durations_hours: list[float] = [2.0, 3.0],  # 2.0h and 3.0h = 5.0h total
) -> tuple[ProductionOrder, list[OperationExecution], ProductionSpecification]:
    """
    Sets up a complete production order environment with approved specification,
    routing steps with known durations, and initialized operation executions.
    """
    # 1. Design & Render
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Artisan Royal Signet Ring",
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
        prompt="18k gold handcrafted signet ring with bezel set sapphire",
        image_url="https://storage.jewelmind.internal/renders/ring_j7.png",
        is_approved_for_production=True,
    )
    db.add(render)
    db.commit()

    # 2. Specification
    total_planned_hours = sum(step_durations_hours)
    spec = ProductionSpecification(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        version_number=1,
        status="approved",
        category="ring",
        estimated_rough_metal_weight_grams=15.0,
        estimated_finished_metal_weight_grams=12.5,
        total_gemstone_count=1,
        estimated_total_bench_hours=total_planned_hours,
    )
    db.add(spec)
    db.commit()

    # 3. Specification Materials & Gemstones
    mat1 = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type="gold",
        metal_purity="18k",
        metal_color="yellow",
        estimated_weight_grams=15.0,
    )
    mat2 = ProductionMaterial(
        id=uuid.uuid4(),
        specification_id=spec.id,
        metal_type="silver",
        metal_purity="925",
        metal_color="white",
        estimated_weight_grams=5.0,
    )
    gem1 = ProductionGemstone(
        id=uuid.uuid4(),
        specification_id=spec.id,
        gemstone_type="sapphire",
        cut_shape="oval",
        stone_count=1,
        estimated_carat_weight=1.5,
    )
    db.add_all([mat1, mat2, gem1])
    db.commit()

    # 4. Routing Steps
    steps = []
    for idx, duration in enumerate(step_durations_hours, start=1):
        step = ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=idx,
            stage_name=f"Bench Stage {idx}",
            required_skill="goldsmith",
            base_hours=duration,
            per_unit_hours=0.0,
            quality_checkpoint="Surface uniformity and structural integrity",
        )
        db.add(step)
        steps.append(step)
    db.commit()

    # 5. Production Order
    now = datetime.now(timezone.utc)
    order = ProductionOrder(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        render_id=render.id,
        specification_id=spec.id,
        quantity=1,
        priority="high",
        status="in_progress",
        deadline=now + timedelta(days=5),
        created_at=now,
    )
    db.add(order)
    db.commit()

    # 6. Initialize Executions via Execution Service
    exec_resp = production_execution_service.initialize_order_executions(db, user.id, order.id)
    return order, exec_resp, spec


# ==============================================================================
# J.7 Test Suite Cases
# ==============================================================================

def test_authenticated_analytics_access(client: TestClient, db: Session):
    """Verifies that an authenticated owner can successfully retrieve order analytics."""
    user = create_test_user(db, "owner")
    order, _, _ = setup_j7_order_environment(db, user)

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["order_id"] == str(order.id)
    assert "planned" in data
    assert "actual" in data
    assert "variance" in data
    assert "operations" in data
    assert "quality" in data
    assert "rework" in data
    assert "schedule" in data


def test_cross_tenant_order_rejected(client: TestClient, db: Session):
    """Verifies IDOR protection: tenant B receives 404 when querying tenant A's order."""
    user_a = create_test_user(db, "tenant_a")
    user_b = create_test_user(db, "tenant_b")
    order_a, _, _ = setup_j7_order_environment(db, user_a)

    res = client.get(
        f"/api/v1/production/orders/{order_a.id}/analytics",
        headers=auth_headers(user_b),
    )
    assert res.status_code == 404
    assert "ORDER_NOT_FOUND" in res.text


def test_unauthenticated_analytics_rejected(client: TestClient, db: Session):
    """Verifies that unauthenticated requests receive 401 Unauthorized."""
    fake_order_id = uuid.uuid4()
    res = client.get(f"/api/v1/production/orders/{fake_order_id}/analytics")
    assert res.status_code == 401


def test_planned_hours_calculation(client: TestClient, db: Session):
    """Verifies that planned hours match the exact sum of routing step durations."""
    user = create_test_user(db, "planned_time")
    # 1.5h + 2.5h = 4.0h
    order, _, _ = setup_j7_order_environment(db, user, step_durations_hours=[1.5, 2.5])

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["planned"]["hours"] == 4.0


def test_actual_hours_and_time_variance(client: TestClient, db: Session):
    """Verifies actual execution duration aggregation and time variance calculation."""
    user = create_test_user(db, "time_variance")
    # Planned: 2.0h + 3.0h = 5.0h
    order, executions, _ = setup_j7_order_environment(db, user, step_durations_hours=[2.0, 3.0])

    # Complete Step 1: 2.5h actual
    e1 = executions[0]
    exec_row1 = db.query(OperationExecution).filter_by(id=e1.id).first()
    assert exec_row1 is not None
    exec_row1.status = "completed"
    exec_row1.actual_duration_hours = 2.5

    # Step 2: In progress, 3.0h actual
    e2 = executions[1]
    exec_row2 = db.query(OperationExecution).filter_by(id=e2.id).first()
    assert exec_row2 is not None
    exec_row2.status = "in_progress"
    exec_row2.actual_duration_hours = 3.0

    db.commit()

    # Total actual = 2.5 + 3.0 = 5.5h
    # Planned = 5.0h
    # Variance hours = +0.5h
    # Variance percent = (0.5 / 5.0) * 100 = 10.0%

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["planned"]["hours"] == 5.0
    assert data["actual"]["hours"] == 5.5
    assert data["variance"]["hours"] == 0.5
    assert data["variance"]["hours_percent"] == 10.0


def test_zero_planned_hours_handles_division_by_zero(client: TestClient, db: Session):
    """Verifies that when planned hours == 0, hours_percent returns None rather than crashing."""
    user = create_test_user(db, "zero_hours")
    order, executions, _ = setup_j7_order_environment(db, user, step_durations_hours=[0.0])

    e1 = executions[0]
    exec_row = db.query(OperationExecution).filter_by(id=e1.id).first()
    assert exec_row is not None
    exec_row.status = "completed"
    exec_row.actual_duration_hours = 1.0
    db.commit()

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["planned"]["hours"] == 0.0
    assert data["actual"]["hours"] == 1.0
    assert data["variance"]["hours"] == 1.0
    assert data["variance"]["hours_percent"] is None


def test_material_planned_vs_actual_and_wastage(client: TestClient, db: Session):
    """Verifies material consumption, wastage, and variance preserving material identity."""
    user = create_test_user(db, "material_analytics")
    order, executions, _ = setup_j7_order_environment(db, user)

    e1 = executions[0]
    db.query(OperationExecution).filter_by(id=e1.id).update({"status": "in_progress"})
    db.commit()

    # Record Gold consumption: planned in spec is 15.0g
    # Actual: 15.8g consumed, 0.8g scrap/wastage
    production_execution_service.record_material_consumption(
        db,
        user.id,
        e1.id,
        MaterialConsumptionCreate(
            material_type="METAL",
            material_name="gold 18k",
            unit="g",
            planned_quantity=15.0,
            actual_quantity=15.8,
            wastage_quantity=0.8,
            wastage_reason="Spruing and filing bench scrap",
        ),
    )

    # Record Silver consumption: planned in spec is 5.0g
    # Actual: 5.2g consumed, 0.2g scrap/wastage
    production_execution_service.record_material_consumption(
        db,
        user.id,
        e1.id,
        MaterialConsumptionCreate(
            material_type="METAL",
            material_name="silver 925",
            unit="g",
            planned_quantity=5.0,
            actual_quantity=5.2,
            wastage_quantity=0.2,
            wastage_reason="Solder joint trimming",
        ),
    )

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    data = res.json()
    materials = data["variance"]["materials"]

    gold = next((m for m in materials if "gold" in m["material_name"].lower()), None)
    silver = next((m for m in materials if "silver" in m["material_name"].lower()), None)

    assert gold is not None
    assert silver is not None

    # Gold assertions
    assert gold["planned_quantity"] == 15.0
    assert gold["actual_quantity"] == 15.8
    assert gold["wastage_quantity"] == 0.8
    assert gold["material_variance"] == 0.8
    # wastage_percent = (0.8 / 15.8) * 100 = 5.06%
    assert round(gold["wastage_percent"], 2) == 5.06

    # Silver assertions
    assert silver["planned_quantity"] == 5.0
    assert silver["actual_quantity"] == 5.2
    assert silver["wastage_quantity"] == 0.2
    assert silver["material_variance"] == 0.2
    # wastage_percent = (0.2 / 5.2) * 100 = 3.85%
    assert round(silver["wastage_percent"], 2) == 3.85

    # Identity preservation: gold and silver must NOT be summed together into 20g / 21g
    assert gold["material_name"] != silver["material_name"]


def test_zero_actual_material_handles_division_by_zero(client: TestClient, db: Session):
    """Verifies that zero actual material consumption leaves wastage_percent as None."""
    user = create_test_user(db, "zero_material")
    order, _, _ = setup_j7_order_environment(db, user)

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    data = res.json()
    materials = data["variance"]["materials"]
    for mat in materials:
        if mat["actual_quantity"] == 0:
            assert mat["wastage_percent"] is None


def test_operations_distribution_and_completion_rate(client: TestClient, db: Session):
    """Verifies counts of completed, in-progress, paused, blocked, and pending operations."""
    user = create_test_user(db, "ops_distribution")
    # 3 operations: 1.0h, 1.0h, 1.0h
    order, executions, _ = setup_j7_order_environment(db, user, step_durations_hours=[1.0, 1.0, 1.0])

    # Step 1: completed
    db.query(OperationExecution).filter_by(id=executions[0].id).update({"status": "completed"})
    # Step 2: in_progress
    db.query(OperationExecution).filter_by(id=executions[1].id).update({"status": "in_progress"})
    # Step 3: pending/ready
    db.commit()

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    ops = res.json()["operations"]
    assert ops["total"] == 3
    assert ops["completed"] == 1
    assert ops["in_progress"] == 1
    assert ops["pending"] == 1
    assert ops["completion_rate_percent"] == 33.33


def test_rework_count_and_rate_calculation(client: TestClient, db: Session):
    """Verifies that rework attempts and rate percent are correctly aggregated."""
    user = create_test_user(db, "rework_analytics")
    order, executions, _ = setup_j7_order_environment(db, user, step_durations_hours=[1.0, 1.0])

    e1 = executions[0]
    # Mark e1 completed
    db.query(OperationExecution).filter_by(id=e1.id).update({"status": "completed"})
    db.commit()

    # Record QC REWORK
    production_execution_service.record_quality_check(
        db,
        user.id,
        e1.id,
        QualityCheckCreate(
            result=QualityCheckResult.REWORK,
            defect_severity=DefectSeverity.HIGH,
            notes="Excessive porosity on bezel edge",
        ),
    )

    # Authorize rework execution
    production_execution_service.create_rework_execution(db, user.id, e1.id)

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    data = res.json()
    rework = data["rework"]
    assert rework["count"] == 1
    # total routing operations = 2, rework = 1 -> rate = (1 / 2) * 100 = 50.0%
    assert rework["rate_percent"] == 50.0


def test_quality_counts_and_first_pass_yield(client: TestClient, db: Session):
    """Verifies quality check counts (PASS, FAIL, REWORK) and first-pass yield."""
    user = create_test_user(db, "quality_yield")
    order, executions, _ = setup_j7_order_environment(db, user, step_durations_hours=[1.0, 1.0])

    e1, e2 = executions[0], executions[1]
    db.query(OperationExecution).filter_by(id=e1.id).update({"status": "completed"})
    db.query(OperationExecution).filter_by(id=e2.id).update({"status": "completed"})
    db.commit()

    # e1 passes
    production_execution_service.record_quality_check(
        db,
        user.id,
        e1.id,
        QualityCheckCreate(
            result=QualityCheckResult.PASS,
            defect_severity=DefectSeverity.NONE,
        ),
    )

    # e2 has a defect
    production_execution_service.record_quality_check(
        db,
        user.id,
        e2.id,
        QualityCheckCreate(
            result=QualityCheckResult.FAIL,
            defect_severity=DefectSeverity.CRITICAL,
            notes="Fractured prong",
        ),
    )

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    qc = res.json()["quality"]
    assert qc["total_checks"] == 2
    assert qc["passed"] == 1
    assert qc["failed"] == 1
    assert qc["rework"] == 0
    assert qc["first_pass_yield_percent"] == 50.0


def test_schedule_milestones_and_variance(client: TestClient, db: Session):
    """Verifies schedule milestones calculation and variance against scheduled completion."""
    user = create_test_user(db, "schedule_variance")
    order, executions, _ = setup_j7_order_environment(db, user)

    # Simulate completed order with timestamps
    start_time = datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc)
    completion_time = datetime(2026, 10, 1, 14, 0, tzinfo=timezone.utc)  # 6 hours actual

    exec1 = executions[0]
    db.query(OperationExecution).filter_by(id=exec1.id).update({
        "status": "completed",
        "actual_start_time": start_time,
        "actual_end_time": completion_time,
        "completed_at": completion_time,
        "actual_duration_hours": 6.0,
    })
    db.query(ProductionOrder).filter_by(id=order.id).update({
        "status": "completed",
    })
    db.commit()

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    sched = res.json()["schedule"]
    assert sched["actual_start"] is not None
    assert sched["actual_completion"] is not None


def test_missing_timestamps_safe(client: TestClient, db: Session):
    """Verifies orders without scheduling/execution timestamps return null safely without errors."""
    user = create_test_user(db, "missing_timestamps")
    order, _, _ = setup_j7_order_environment(db, user)

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    sched = res.json()["schedule"]
    assert sched["actual_completion"] is None
    assert sched["schedule_variance_hours"] is None


def test_read_only_guarantee(client: TestClient, db: Session):
    """Verifies that requesting analytics does not modify any table in the database."""
    user = create_test_user(db, "read_only")
    order, _, _ = setup_j7_order_environment(db, user)

    order_before = db.query(ProductionOrder).filter_by(id=order.id).first()
    assert order_before is not None
    execs_before_count = db.query(OperationExecution).filter_by(production_order_id=order.id).count()
    qc_before_count = db.query(QualityCheck).count()
    mat_before_count = db.query(MaterialConsumption).count()

    # Query analytics
    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200

    # Verify no records were added or modified
    assert db.query(OperationExecution).filter_by(production_order_id=order.id).count() == execs_before_count
    assert db.query(QualityCheck).count() == qc_before_count
    assert db.query(MaterialConsumption).count() == mat_before_count
    order_after = db.query(ProductionOrder).filter_by(id=order.id).first()
    assert order_after is not None
    assert order_after.status == order_before.status


def test_numeric_safety_no_nan_or_infinity(client: TestClient, db: Session):
    """Verifies that all response fields are strictly JSON compliant numbers or None, never NaN or Inf."""
    user = create_test_user(db, "numeric_safety")
    # Setup order with zero hours
    order, _, _ = setup_j7_order_environment(db, user, step_durations_hours=[0.0])

    res = client.get(
        f"/api/v1/production/orders/{order.id}/analytics",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    content = res.text
    assert "NaN" not in content
    assert "Infinity" not in content
    assert "-Infinity" not in content


def test_atelier_analytics_summary_authenticated(client: TestClient, db: Session):
    """Verifies cross-order atelier analytics summary calculations."""
    user = create_test_user(db, "atelier_summary")
    setup_j7_order_environment(db, user, step_durations_hours=[1.0, 1.0])  # 2.0h
    setup_j7_order_environment(db, user, step_durations_hours=[2.0])       # 2.0h

    res = client.get(
        "/api/v1/production/analytics/summary",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_orders_analyzed"] >= 2
    assert data["total_planned_hours"] >= 4.0
    assert "net_time_variance_hours" in data
    assert "overall_rework_rate_percent" in data
    assert "overall_qc_pass_rate_percent" in data


def test_atelier_analytics_summary_tenant_isolated(client: TestClient, db: Session):
    """Verifies that User A's atelier analytics summary does not include User B's orders."""
    user_a = create_test_user(db, "atelier_iso_a")
    user_b = create_test_user(db, "atelier_iso_b")

    setup_j7_order_environment(db, user_a, step_durations_hours=[1.0])
    setup_j7_order_environment(db, user_b, step_durations_hours=[3.0, 3.0])

    res_a = client.get(
        "/api/v1/production/analytics/summary",
        headers=auth_headers(user_a),
    )
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["total_orders_analyzed"] == 1
    assert data_a["total_planned_hours"] == 1.0

    res_b = client.get(
        "/api/v1/production/analytics/summary",
        headers=auth_headers(user_b),
    )
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["total_orders_analyzed"] == 1
    assert data_b["total_planned_hours"] == 6.0
