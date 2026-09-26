"""
Phase J.3 Test Suite — Worker & Machine Execution
Comprehensive tests covering artisan skill matching, equipment compatibility,
resource conflict detection, planned vs actual resource tracking,
reassignment boundaries, and concurrency protection.
"""

import math
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token
from app.models.design import Design, DesignRender
from app.models.execution import OperationExecution
from app.models.production import Machine, ProductionOrder, Worker
from app.models.schedule import ProductionSchedule, ScheduledTask
from app.models.specification import (
    ProductionMaterial,
    ProductionSpecification,
    ProductionStep,
)
from app.models.user import User
from app.schemas.auth import UserCreate
from app.schemas.execution import (
    ExecutionStatus,
    MachineAssignmentRequest,
    OperationExecutionCreate,
    OperationExecutionTransitionRequest,
    WorkerAssignmentRequest,
)
from app.services.production_execution_service import (
    is_machine_compatible,
    is_worker_skill_eligible,
    production_execution_service,
)
from app.services.user_service import user_service


# ==============================================================================
# Test Fixtures & Helpers
# ==============================================================================

def create_test_user(db: Session, email_prefix: str = "artisan") -> User:
    """Creates a unique test user in the database."""
    unique_email = f"{email_prefix}.{uuid.uuid4().hex[:8]}@jewelmind.atelier"
    return user_service.create(
        db,
        UserCreate(
            email=unique_email,
            password="SecurePassword123!",
            full_name=f"Master Artisan {email_prefix.title()}",
        ),
    )


def auth_headers(user: User) -> dict:
    """Generates bearer authorization headers for a user."""
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def setup_complete_order_environment(
    db: Session,
    user: User,
    num_steps: int = 3,
    with_schedule: bool = False,
) -> Tuple[Design, DesignRender, ProductionSpecification, ProductionOrder, List[ProductionStep], List[ScheduledTask]]:
    """
    Sets up an approved Design, approved Render, approved Specification with N steps,
    and a spec-backed ProductionOrder.
    """
    design = Design(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Solitaire Diamond Ring",
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
        image_url="https://storage.jewelmind.internal/renders/solitaire.png",
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
        estimated_rough_metal_weight_grams=6.0,
        estimated_finished_metal_weight_grams=5.2,
        total_gemstone_count=1,
        estimated_total_bench_hours=5.0,
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
        estimated_weight_grams=6.0,
    )
    db.add(material)

    steps: List[ProductionStep] = []
    step_defs = [
        ("Casting & Tree Preparation", "casting", "casting_furnace", 1.5, 0.25),
        ("Stone Setting (Collet)", "stone_setting", None, 2.0, 0.5),
        ("Hand Polishing & Ultrasonic Clean", "polishing", "polishing_lathe", 1.0, 0.2),
        ("Laser Hallmark Engraving", "engraving", "laser_engraver", 0.5, 0.1),
    ]

    for i in range(min(num_steps, len(step_defs))):
        name, skill, machine, base_h, per_unit_h = step_defs[i]
        step = ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=i + 1,
            stage_name=name,
            required_skill=skill,
            required_machine_type=machine,
            base_hours=base_h,
            per_unit_hours=per_unit_h,
            quality_checkpoint=f"QC inspection for {name}",
        )
        db.add(step)
        steps.append(step)
    db.commit()

    order = ProductionOrder(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        quantity=2,
        priority="high",
        status="pending",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        notes="High-precision wedding client",
        render_id=render.id,
        approved_render_url=render.image_url,
        specification_id=spec.id,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    scheduled_tasks: List[ScheduledTask] = []
    if with_schedule:
        schedule = ProductionSchedule(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Test Schedule",
            start_date=datetime.now(timezone.utc),
            horizon_days=14,
            solver_status="OPTIMAL",
            makespan_hours=8.0,
        )
        db.add(schedule)
        db.commit()

        start_cursor = datetime.now(timezone.utc) + timedelta(hours=1)
        for idx, st in enumerate(steps):
            dur = max(1.0, float(math.ceil(st.base_hours + st.per_unit_hours * order.quantity)))
            end_cursor = start_cursor + timedelta(hours=dur)
            task = ScheduledTask(
                id=uuid.uuid4(),
                schedule_id=schedule.id,
                order_id=order.id,
                operation_name=st.stage_name,
                start_time=start_cursor,
                end_time=end_cursor,
                duration_hours=dur,
                sequence_order=idx + 1,
                is_overdue=False,
            )
            db.add(task)
            scheduled_tasks.append(task)
            start_cursor = end_cursor
        db.commit()

    return design, render, spec, order, steps, scheduled_tasks


# ==============================================================================
# SECTION A: WORKER ASSIGNMENT (Tests 1 to 6)
# ==============================================================================

def test_j3_01_assign_valid_worker(client: TestClient, db_session: Session):
    """Test 1: Assign valid worker with matching skill via backend and API."""
    user = create_test_user(db_session, "j3_w1")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Goldsmith", skill="casting")
    db_session.add(worker)
    db_session.commit()

    _, _, _, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex = executions[0]

    # Service method assignment
    assigned = production_execution_service.assign_worker(
        db=db_session,
        user_id=user.id,
        execution_id=step1_ex.id,
        worker_id=worker.id,
    )
    assert assigned.worker_id == worker.id
    assert assigned.worker.name == "Rahul Goldsmith"

    # API route assignment
    headers = auth_headers(user)
    resp = client.post(
        f"/api/v1/production/executions/{step1_ex.id}/assign-worker",
        headers=headers,
        json={"worker_id": str(worker.id)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["worker_id"] == str(worker.id)
    assert data["actual_worker_id"] == str(worker.id)
    assert data["worker_name"] == "Rahul Goldsmith"
    assert data["worker_eligible"] is True


def test_j3_02_reject_cross_tenant_worker(client: TestClient, db_session: Session):
    """Test 2: Tenant A attempts to assign Tenant B's worker -> 404 WORKER_NOT_FOUND."""
    user_a = create_test_user(db_session, "j3_tenant_a")
    user_b = create_test_user(db_session, "j3_tenant_b")

    worker_b = Worker(id=uuid.uuid4(), user_id=user_b.id, name="Foreign Artisan", skill="casting")
    db_session.add(worker_b)
    db_session.commit()

    _, _, _, order_a, _, _ = setup_complete_order_environment(db_session, user_a, num_steps=1)
    executions_a = production_execution_service.initialize_order_executions(db_session, user_a.id, order_a.id)
    ex_a = executions_a[0]

    # Service call rejected
    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_worker(
            db=db_session,
            user_id=user_a.id,
            execution_id=ex_a.id,
            worker_id=worker_b.id,
        )
    assert exc_info.value.code == "WORKER_NOT_FOUND"
    assert exc_info.value.status_code == 404

    # API call rejected without revealing Tenant B existence
    headers_a = auth_headers(user_a)
    resp = client.post(
        f"/api/v1/production/executions/{ex_a.id}/assign-worker",
        headers=headers_a,
        json={"worker_id": str(worker_b.id)},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "WORKER_NOT_FOUND"


def test_j3_03_reject_nonexistent_worker(client: TestClient, db_session: Session):
    """Test 3: Assigning a random nonexistent UUID worker returns 404."""
    user = create_test_user(db_session, "j3_nonexist_w")
    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    fake_worker_id = uuid.uuid4()
    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_worker(
            db=db_session,
            user_id=user.id,
            execution_id=ex.id,
            worker_id=fake_worker_id,
        )
    assert exc_info.value.code == "WORKER_NOT_FOUND"
    assert exc_info.value.status_code == 404

    headers = auth_headers(user)
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/assign-worker",
        headers=headers,
        json={"worker_id": str(fake_worker_id)},
    )
    assert resp.status_code == 404


def test_j3_04_reject_worker_without_required_skill(client: TestClient, db_session: Session):
    """Test 4: Assigning a worker lacking the required craft skill -> 409 WORKER_INELIGIBLE_SKILL."""
    user = create_test_user(db_session, "j3_wrong_skill")
    polisher = Worker(id=uuid.uuid4(), user_id=user.id, name="Amit Polisher", skill="polishing")
    db_session.add(polisher)
    db_session.commit()

    # Step 1 requires "casting"
    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_worker(
            db=db_session,
            user_id=user.id,
            execution_id=ex.id,
            worker_id=polisher.id,
        )
    assert exc_info.value.code == "WORKER_INELIGIBLE_SKILL"
    assert exc_info.value.status_code == 409

    headers = auth_headers(user)
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/assign-worker",
        headers=headers,
        json={"worker_id": str(polisher.id)},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "WORKER_INELIGIBLE_SKILL"


def test_j3_05_reject_assignment_to_completed_execution(db_session: Session):
    """Test 5: Completed executions are terminal and reject worker assignment."""
    user = create_test_user(db_session, "j3_comp_assign")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Caster", skill="casting")
    machine = Machine(id=uuid.uuid4(), user_id=user.id, name="Casting Rig", machine_type="casting_furnace")
    db_session.add_all([worker, machine])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    # Start and complete
    production_execution_service.assign_worker(db_session, user.id, ex.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, ex.id, machine.id)
    production_execution_service.transition_execution(
        db_session, user.id, ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED)
    )

    # Attempt assignment on completed execution
    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_worker(
            db=db_session,
            user_id=user.id,
            execution_id=ex.id,
            worker_id=worker.id,
        )
    assert exc_info.value.code == "EXECUTION_ALREADY_COMPLETED"
    assert exc_info.value.status_code == 409


def test_j3_06_worker_remains_assigned_after_refresh(db_session: Session):
    """Test 6: Valid worker remains assigned upon refresh and query reloading."""
    user = create_test_user(db_session, "j3_persist_w")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Goldsmith", skill="casting")
    db_session.add(worker)
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    production_execution_service.assign_worker(db_session, user.id, ex.id, worker.id)

    db_session.expire_all()
    reloaded = production_execution_service.get_execution_by_id(db_session, user.id, ex.id)
    assert reloaded.worker_id == worker.id
    assert reloaded.worker is not None
    assert reloaded.worker.name == "Rahul Goldsmith"


# ==============================================================================
# SECTION B: MACHINE ASSIGNMENT (Tests 7 to 11)
# ==============================================================================

def test_j3_07_assign_valid_machine(client: TestClient, db_session: Session):
    """Test 7: Assign compatible machine via backend and API."""
    user = create_test_user(db_session, "j3_m1")
    machine = Machine(id=uuid.uuid4(), user_id=user.id, name="Precision Furnace #1", machine_type="casting_furnace")
    db_session.add(machine)
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    # Service method assignment
    assigned = production_execution_service.assign_machine(
        db=db_session,
        user_id=user.id,
        execution_id=ex.id,
        machine_id=machine.id,
    )
    assert assigned.machine_id == machine.id
    assert assigned.machine.name == "Precision Furnace #1"

    # API route assignment
    headers = auth_headers(user)
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/assign-machine",
        headers=headers,
        json={"machine_id": str(machine.id)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["machine_id"] == str(machine.id)
    assert data["actual_machine_id"] == str(machine.id)
    assert data["machine_name"] == "Precision Furnace #1"
    assert data["machine_compatible"] is True


def test_j3_08_reject_cross_tenant_machine(client: TestClient, db_session: Session):
    """Test 8: Tenant A cannot assign Tenant B's machine -> 404 MACHINE_NOT_FOUND."""
    user_a = create_test_user(db_session, "j3_tenant_ma")
    user_b = create_test_user(db_session, "j3_tenant_mb")

    machine_b = Machine(id=uuid.uuid4(), user_id=user_b.id, name="User B Lathe", machine_type="casting_furnace")
    db_session.add(machine_b)
    db_session.commit()

    _, _, _, order_a, _, _ = setup_complete_order_environment(db_session, user_a, num_steps=1)
    executions_a = production_execution_service.initialize_order_executions(db_session, user_a.id, order_a.id)
    ex_a = executions_a[0]

    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_machine(
            db=db_session,
            user_id=user_a.id,
            execution_id=ex_a.id,
            machine_id=machine_b.id,
        )
    assert exc_info.value.code == "MACHINE_NOT_FOUND"
    assert exc_info.value.status_code == 404

    headers_a = auth_headers(user_a)
    resp = client.post(
        f"/api/v1/production/executions/{ex_a.id}/assign-machine",
        headers=headers_a,
        json={"machine_id": str(machine_b.id)},
    )
    assert resp.status_code == 404


def test_j3_09_reject_nonexistent_machine(client: TestClient, db_session: Session):
    """Test 9: Assigning a random nonexistent UUID machine returns 404."""
    user = create_test_user(db_session, "j3_nonexist_m")
    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    fake_id = uuid.uuid4()
    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_machine(
            db=db_session,
            user_id=user.id,
            execution_id=ex.id,
            machine_id=fake_id,
        )
    assert exc_info.value.code == "MACHINE_NOT_FOUND"
    assert exc_info.value.status_code == 404

    headers = auth_headers(user)
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/assign-machine",
        headers=headers,
        json={"machine_id": str(fake_id)},
    )
    assert resp.status_code == 404


def test_j3_10_reject_incompatible_machine_type(client: TestClient, db_session: Session):
    """Test 10: Assigning equipment with incompatible functional type -> 409 MACHINE_INCOMPATIBLE_TYPE."""
    user = create_test_user(db_session, "j3_wrong_machine")
    engraver = Machine(id=uuid.uuid4(), user_id=user.id, name="Fiber Laser", machine_type="laser_engraver")
    db_session.add(engraver)
    db_session.commit()

    # Step 1 requires "casting_furnace"
    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_machine(
            db=db_session,
            user_id=user.id,
            execution_id=ex.id,
            machine_id=engraver.id,
        )
    assert exc_info.value.code == "MACHINE_INCOMPATIBLE_TYPE"
    assert exc_info.value.status_code == 409

    headers = auth_headers(user)
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/assign-machine",
        headers=headers,
        json={"machine_id": str(engraver.id)},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "MACHINE_INCOMPATIBLE_TYPE"


def test_j3_11_reject_machine_assignment_to_completed_execution(db_session: Session):
    """Test 11: Completed executions are terminal and reject machine assignment."""
    user = create_test_user(db_session, "j3_comp_mach")
    machine = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Caster", skill="casting")
    db_session.add_all([machine, worker])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    # Start and complete
    production_execution_service.assign_worker(db_session, user.id, ex.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, ex.id, machine.id)
    production_execution_service.transition_execution(
        db_session, user.id, ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED)
    )

    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_machine(
            db=db_session,
            user_id=user.id,
            execution_id=ex.id,
            machine_id=machine.id,
        )
    assert exc_info.value.code == "EXECUTION_ALREADY_COMPLETED"
    assert exc_info.value.status_code == 409


# ==============================================================================
# SECTION C: START REQUIREMENTS VALIDATION (Tests 12 to 17)
# ==============================================================================

def test_j3_12_worker_required_but_missing_rejects_start(client: TestClient, db_session: Session):
    """Test 12: Starting an operation without an assigned worker when required -> 409 MISSING_REQUIRED_WORKER."""
    user = create_test_user(db_session, "j3_miss_w")
    # Workshop has workers registered
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul", skill="casting")
    db_session.add(worker)
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]
    assert ex.worker_id is None

    # Service call rejected
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db=db_session,
            user_id=user.id,
            execution_id=ex.id,
            req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "MISSING_REQUIRED_WORKER"
    assert exc_info.value.status_code == 409

    # API call rejected
    headers = auth_headers(user)
    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/transition",
        headers=headers,
        json={"target_status": "in_progress"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "MISSING_REQUIRED_WORKER"


def test_j3_13_machine_required_but_missing_rejects_start(client: TestClient, db_session: Session):
    """Test 13: Starting an operation without assigned machine when required -> 409 MISSING_REQUIRED_MACHINE."""
    user = create_test_user(db_session, "j3_miss_m")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul", skill="casting")
    machine = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([worker, machine])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    # Assign worker only
    production_execution_service.assign_worker(db_session, user.id, ex.id, worker.id)

    # Attempt to start without machine
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db=db_session,
            user_id=user.id,
            execution_id=ex.id,
            req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "MISSING_REQUIRED_MACHINE"
    assert exc_info.value.status_code == 409


def test_j3_14_both_required_and_present_start_succeeds(client: TestClient, db_session: Session):
    """Test 14: Both required worker and machine present -> start succeeds."""
    user = create_test_user(db_session, "j3_start_ok")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul", skill="casting")
    machine = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([worker, machine])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    production_execution_service.assign_worker(db_session, user.id, ex.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, ex.id, machine.id)

    started = production_execution_service.transition_execution(
        db=db_session,
        user_id=user.id,
        execution_id=ex.id,
        req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    assert started.status == "in_progress"
    assert started.actual_start_time is not None
    assert started.worker_id == worker.id
    assert started.machine_id == machine.id


def test_j3_15_operation_requiring_neither_resource_starts_correctly(db_session: Session):
    """Test 15: Operation requiring neither artisan nor machine starts without resources."""
    user = create_test_user(db_session, "j3_no_res")
    design = Design(id=uuid.uuid4(), user_id=user.id, name="Manual Ring", category="ring")
    render = DesignRender(id=uuid.uuid4(), design_id=design.id, user_id=user.id, version_number=1, render_mode="text", prompt="ring", image_url="https://x.com/r.png")
    spec = ProductionSpecification(id=uuid.uuid4(), user_id=user.id, design_id=design.id, render_id=render.id, version_number=1, status="approved", category="ring")
    db_session.add_all([design, render, spec])
    db_session.commit()

    # Step with no required machine and skill='none' or 'general'
    step = ProductionStep(
        id=uuid.uuid4(),
        specification_id=spec.id,
        step_number=1,
        stage_name="Visual Quality Audit",
        required_skill="none",
        required_machine_type=None,
        base_hours=0.5,
        per_unit_hours=0.0,
    )
    db_session.add(step)
    db_session.commit()

    order = ProductionOrder(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        quantity=1,
        priority="medium",
        status="pending",
        deadline=datetime.now(timezone.utc) + timedelta(days=3),
        specification_id=spec.id,
    )
    db_session.add(order)
    db_session.commit()

    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    # Starts correctly with neither resource
    started = production_execution_service.transition_execution(
        db=db_session,
        user_id=user.id,
        execution_id=ex.id,
        req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    assert started.status == "in_progress"
    assert started.actual_start_time is not None


def test_j3_16_invalid_worker_with_valid_machine_rejects_start(db_session: Session):
    """Test 16: Invalid worker skill with valid machine -> rejected on start."""
    user = create_test_user(db_session, "j3_inval_w")
    polisher = Worker(id=uuid.uuid4(), user_id=user.id, name="Amit Polisher", skill="polishing")
    furnace = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([polisher, furnace])
    db_session.commit()

    # Step requires "casting"
    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    # Manually attach worker (simulating legacy or direct assignment bypass)
    ex.worker_id = polisher.id
    ex.machine_id = furnace.id
    db_session.commit()

    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db=db_session,
            user_id=user.id,
            execution_id=ex.id,
            req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "WORKER_INELIGIBLE_SKILL"
    assert exc_info.value.status_code == 409


def test_j3_17_valid_worker_with_invalid_machine_rejects_start(db_session: Session):
    """Test 17: Valid worker with incompatible machine type -> rejected on start."""
    user = create_test_user(db_session, "j3_inval_m")
    caster = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    lathe = Machine(id=uuid.uuid4(), user_id=user.id, name="Polishing Lathe", machine_type="polishing_lathe")
    db_session.add_all([caster, lathe])
    db_session.commit()

    # Step requires "casting_furnace"
    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    ex.worker_id = caster.id
    ex.machine_id = lathe.id
    db_session.commit()

    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db=db_session,
            user_id=user.id,
            execution_id=ex.id,
            req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "MACHINE_INCOMPATIBLE_TYPE"
    assert exc_info.value.status_code == 409


# ==============================================================================
# SECTION D: WORKER RESOURCE CONFLICT (Tests 18 to 20)
# ==============================================================================

def test_j3_18_worker_executing_operation_a_cannot_start_operation_b(db_session: Session):
    """Test 18: Worker actively in IN_PROGRESS on Op A cannot start Op B."""
    user = create_test_user(db_session, "j3_w_conflict")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Goldsmith", skill="casting")
    furnace1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    furnace2 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Beta", machine_type="casting_furnace")
    db_session.add_all([worker, furnace1, furnace2])
    db_session.commit()

    # Order 1 & Order 2
    _, _, _, order1, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    _, _, _, order2, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    execs1 = production_execution_service.initialize_order_executions(db_session, user.id, order1.id)
    execs2 = production_execution_service.initialize_order_executions(db_session, user.id, order2.id)

    op_a = execs1[0]
    op_b = execs2[0]

    # Start Op A with Rahul + Furnace 1
    production_execution_service.assign_worker(db_session, user.id, op_a.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, op_a.id, furnace1.id)
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    assert op_a.status == "in_progress"

    # Assign Rahul + Furnace 2 to Op B
    production_execution_service.assign_worker(db_session, user.id, op_b.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, op_b.id, furnace2.id)

    # Attempting to start Op B must be rejected due to worker conflict
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db=db_session,
            user_id=user.id,
            execution_id=op_b.id,
            req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "WORKER_RESOURCE_CONFLICT"
    assert exc_info.value.status_code == 409


def test_j3_19_worker_becomes_available_after_operation_a_completes(db_session: Session):
    """Test 19: Worker is released when Op A completes, enabling Op B to start."""
    user = create_test_user(db_session, "j3_w_release")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Goldsmith", skill="casting")
    furnace1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    furnace2 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Beta", machine_type="casting_furnace")
    db_session.add_all([worker, furnace1, furnace2])
    db_session.commit()

    _, _, _, order1, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    _, _, _, order2, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    op_a = production_execution_service.initialize_order_executions(db_session, user.id, order1.id)[0]
    op_b = production_execution_service.initialize_order_executions(db_session, user.id, order2.id)[0]

    production_execution_service.assign_worker(db_session, user.id, op_a.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, op_a.id, furnace1.id)
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )

    production_execution_service.assign_worker(db_session, user.id, op_b.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, op_b.id, furnace2.id)

    # Complete Op A
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED)
    )
    assert op_a.status == "completed"

    # Now Op B can successfully start with Rahul
    started_b = production_execution_service.transition_execution(
        db_session, user.id, op_b.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    assert started_b.status == "in_progress"
    assert started_b.worker_id == worker.id


def test_j3_20_paused_operation_continues_reserving_worker(db_session: Session):
    """Test 20: Paused operation continues reserving worker; Op B cannot claim worker while Op A is paused."""
    user = create_test_user(db_session, "j3_w_paused")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Goldsmith", skill="casting")
    furnace1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    furnace2 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Beta", machine_type="casting_furnace")
    db_session.add_all([worker, furnace1, furnace2])
    db_session.commit()

    _, _, _, order1, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    _, _, _, order2, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    op_a = production_execution_service.initialize_order_executions(db_session, user.id, order1.id)[0]
    op_b = production_execution_service.initialize_order_executions(db_session, user.id, order2.id)[0]

    production_execution_service.assign_worker(db_session, user.id, op_a.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, op_a.id, furnace1.id)
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )

    # Pause Op A
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.PAUSED)
    )
    assert op_a.status == "paused"

    # Op B attempts to start with Worker Rahul
    production_execution_service.assign_worker(db_session, user.id, op_b.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, op_b.id, furnace2.id)

    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db=db_session,
            user_id=user.id,
            execution_id=op_b.id,
            req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "WORKER_RESOURCE_CONFLICT"
    assert exc_info.value.status_code == 409


# ==============================================================================
# SECTION E: MACHINE RESOURCE CONFLICT (Tests 21 to 23)
# ==============================================================================

def test_j3_21_machine_executing_operation_a_cannot_start_operation_b(db_session: Session):
    """Test 21: Equipment in IN_PROGRESS on Op A cannot start Op B."""
    user = create_test_user(db_session, "j3_m_conflict")
    worker1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    worker2 = Worker(id=uuid.uuid4(), user_id=user.id, name="Sunil Caster", skill="casting")
    machine = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([worker1, worker2, machine])
    db_session.commit()

    _, _, _, order1, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    _, _, _, order2, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    op_a = production_execution_service.initialize_order_executions(db_session, user.id, order1.id)[0]
    op_b = production_execution_service.initialize_order_executions(db_session, user.id, order2.id)[0]

    # Start Op A with Worker 1 + Machine
    production_execution_service.assign_worker(db_session, user.id, op_a.id, worker1.id)
    production_execution_service.assign_machine(db_session, user.id, op_a.id, machine.id)
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )

    # Assign Worker 2 + same Machine to Op B
    production_execution_service.assign_worker(db_session, user.id, op_b.id, worker2.id)
    production_execution_service.assign_machine(db_session, user.id, op_b.id, machine.id)

    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db=db_session,
            user_id=user.id,
            execution_id=op_b.id,
            req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "MACHINE_RESOURCE_CONFLICT"
    assert exc_info.value.status_code == 409


def test_j3_22_machine_becomes_available_after_completion(db_session: Session):
    """Test 22: Equipment is released when Op A completes, enabling Op B to start."""
    user = create_test_user(db_session, "j3_m_release")
    worker1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    worker2 = Worker(id=uuid.uuid4(), user_id=user.id, name="Sunil Caster", skill="casting")
    machine = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([worker1, worker2, machine])
    db_session.commit()

    _, _, _, order1, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    _, _, _, order2, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    op_a = production_execution_service.initialize_order_executions(db_session, user.id, order1.id)[0]
    op_b = production_execution_service.initialize_order_executions(db_session, user.id, order2.id)[0]

    production_execution_service.assign_worker(db_session, user.id, op_a.id, worker1.id)
    production_execution_service.assign_machine(db_session, user.id, op_a.id, machine.id)
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )

    production_execution_service.assign_worker(db_session, user.id, op_b.id, worker2.id)
    production_execution_service.assign_machine(db_session, user.id, op_b.id, machine.id)

    # Complete Op A
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED)
    )

    # Op B can now start
    started_b = production_execution_service.transition_execution(
        db_session, user.id, op_b.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    assert started_b.status == "in_progress"
    assert started_b.machine_id == machine.id


def test_j3_23_paused_operation_continues_reserving_machine(db_session: Session):
    """Test 23: Paused operation reserves equipment; Op B cannot claim machine while Op A is paused."""
    user = create_test_user(db_session, "j3_m_paused")
    worker1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    worker2 = Worker(id=uuid.uuid4(), user_id=user.id, name="Sunil Caster", skill="casting")
    machine = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([worker1, worker2, machine])
    db_session.commit()

    _, _, _, order1, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    _, _, _, order2, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    op_a = production_execution_service.initialize_order_executions(db_session, user.id, order1.id)[0]
    op_b = production_execution_service.initialize_order_executions(db_session, user.id, order2.id)[0]

    production_execution_service.assign_worker(db_session, user.id, op_a.id, worker1.id)
    production_execution_service.assign_machine(db_session, user.id, op_a.id, machine.id)
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )

    # Pause Op A
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.PAUSED)
    )

    production_execution_service.assign_worker(db_session, user.id, op_b.id, worker2.id)
    production_execution_service.assign_machine(db_session, user.id, op_b.id, machine.id)

    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db=db_session,
            user_id=user.id,
            execution_id=op_b.id,
            req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "MACHINE_RESOURCE_CONFLICT"
    assert exc_info.value.status_code == 409


# ==============================================================================
# SECTION F: AUTOMATIC PROGRESSION RESOURCE INDEPENDENCE (Tests 24 to 28)
# ==============================================================================

def test_j3_24_step1_completion_advances_step2_to_ready(db_session: Session):
    """Test 24: Step 1 completion automatically transitions Step 2 to READY."""
    user = create_test_user(db_session, "j3_prog_ready")
    w1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    m1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([w1, m1])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex = executions[0], executions[1]

    production_execution_service.assign_worker(db_session, user.id, step1_ex.id, w1.id)
    production_execution_service.assign_machine(db_session, user.id, step1_ex.id, m1.id)
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED)
    )

    db_session.refresh(step2_ex)
    assert step2_ex.status == "ready"


def test_j3_25_step2_does_not_inherit_step1_worker(db_session: Session):
    """Test 25: Step 2 does NOT automatically inherit Step 1's worker."""
    user = create_test_user(db_session, "j3_no_w_inherit")
    w1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    m1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([w1, m1])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex = executions[0], executions[1]

    production_execution_service.assign_worker(db_session, user.id, step1_ex.id, w1.id)
    production_execution_service.assign_machine(db_session, user.id, step1_ex.id, m1.id)
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED)
    )

    db_session.refresh(step2_ex)
    assert step2_ex.worker_id != w1.id
    assert step2_ex.worker_id is None


def test_j3_26_step2_does_not_inherit_step1_machine(db_session: Session):
    """Test 26: Step 2 does NOT automatically inherit Step 1's machine."""
    user = create_test_user(db_session, "j3_no_m_inherit")
    w1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    m1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([w1, m1])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex = executions[0], executions[1]

    production_execution_service.assign_worker(db_session, user.id, step1_ex.id, w1.id)
    production_execution_service.assign_machine(db_session, user.id, step1_ex.id, m1.id)
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED)
    )

    db_session.refresh(step2_ex)
    assert step2_ex.machine_id != m1.id
    assert step2_ex.machine_id is None


def test_j3_27_step2_can_use_different_eligible_worker(db_session: Session):
    """Test 27: Step 2 independently assigns and executes with an eligible worker (Priya: stone_setting)."""
    user = create_test_user(db_session, "j3_step2_worker")
    w1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    w2 = Worker(id=uuid.uuid4(), user_id=user.id, name="Priya Setter", skill="stone_setting")
    m1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([w1, w2, m1])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex = executions[0], executions[1]

    # Step 1 execution
    production_execution_service.assign_worker(db_session, user.id, step1_ex.id, w1.id)
    production_execution_service.assign_machine(db_session, user.id, step1_ex.id, m1.id)
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED)
    )

    # Step 2: assign Priya
    assigned_step2 = production_execution_service.assign_worker(db_session, user.id, step2_ex.id, w2.id)
    assert assigned_step2.worker_id == w2.id
    assert assigned_step2.worker.name == "Priya Setter"

    # Start Step 2 (Stone setting requires no machine)
    started_step2 = production_execution_service.transition_execution(
        db_session, user.id, step2_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    assert started_step2.status == "in_progress"
    assert started_step2.worker_id == w2.id


def test_j3_28_step2_can_use_different_compatible_machine(db_session: Session):
    """Test 28: Step 3 uses Polishing Lathe while Step 1 used Casting Furnace."""
    user = create_test_user(db_session, "j3_step3_machine")
    w1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    w2 = Worker(id=uuid.uuid4(), user_id=user.id, name="Priya Setter", skill="stone_setting")
    w3 = Worker(id=uuid.uuid4(), user_id=user.id, name="Amit Polisher", skill="polishing")
    m1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    m3 = Machine(id=uuid.uuid4(), user_id=user.id, name="High-Speed Lathe", machine_type="polishing_lathe")
    db_session.add_all([w1, w2, w3, m1, m3])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=3)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex, step3_ex = executions[0], executions[1], executions[2]

    # Complete Step 1
    production_execution_service.assign_worker(db_session, user.id, step1_ex.id, w1.id)
    production_execution_service.assign_machine(db_session, user.id, step1_ex.id, m1.id)
    production_execution_service.transition_execution(db_session, user.id, step1_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS))
    production_execution_service.transition_execution(db_session, user.id, step1_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED))

    # Complete Step 2
    production_execution_service.assign_worker(db_session, user.id, step2_ex.id, w2.id)
    production_execution_service.transition_execution(db_session, user.id, step2_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS))
    production_execution_service.transition_execution(db_session, user.id, step2_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED))

    # Step 3: Assign Polisher and Polishing Lathe
    production_execution_service.assign_worker(db_session, user.id, step3_ex.id, w3.id)
    production_execution_service.assign_machine(db_session, user.id, step3_ex.id, m3.id)

    started_step3 = production_execution_service.transition_execution(
        db_session, user.id, step3_ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    assert started_step3.status == "in_progress"
    assert started_step3.worker_id == w3.id
    assert started_step3.machine_id == m3.id


# ==============================================================================
# SECTION G: REASSIGNMENT (Tests 29 to 33)
# ==============================================================================

def test_j3_29_ready_execution_can_reassign_worker(db_session: Session):
    """Test 29: In READY state, worker assignment can be changed to another eligible worker."""
    user = create_test_user(db_session, "j3_reassign_ready_w")
    w1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    w2 = Worker(id=uuid.uuid4(), user_id=user.id, name="Sunil Caster", skill="casting")
    db_session.add_all([w1, w2])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    ex = production_execution_service.initialize_order_executions(db_session, user.id, order.id)[0]

    # Assign w1
    production_execution_service.assign_worker(db_session, user.id, ex.id, w1.id)
    assert ex.worker_id == w1.id

    # Reassign to w2 in READY
    production_execution_service.assign_worker(db_session, user.id, ex.id, w2.id)
    assert ex.worker_id == w2.id
    assert ex.worker.name == "Sunil Caster"


def test_j3_30_ready_execution_can_reassign_machine(db_session: Session):
    """Test 30: In READY state, machine assignment can be changed to another compatible machine."""
    user = create_test_user(db_session, "j3_reassign_ready_m")
    m1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    m2 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Beta", machine_type="casting_furnace")
    db_session.add_all([m1, m2])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    ex = production_execution_service.initialize_order_executions(db_session, user.id, order.id)[0]

    production_execution_service.assign_machine(db_session, user.id, ex.id, m1.id)
    assert ex.machine_id == m1.id

    production_execution_service.assign_machine(db_session, user.id, ex.id, m2.id)
    assert ex.machine_id == m2.id
    assert ex.machine.name == "Furnace Beta"


def test_j3_31_in_progress_reassignment_rejected(db_session: Session):
    """Test 31: Reassigning worker or machine while IN_PROGRESS is rejected -> 409 REASSIGNMENT_NOT_ALLOWED."""
    user = create_test_user(db_session, "j3_reassign_inprog")
    w1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    w2 = Worker(id=uuid.uuid4(), user_id=user.id, name="Sunil Caster", skill="casting")
    m1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([w1, w2, m1])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    ex = production_execution_service.initialize_order_executions(db_session, user.id, order.id)[0]

    production_execution_service.assign_worker(db_session, user.id, ex.id, w1.id)
    production_execution_service.assign_machine(db_session, user.id, ex.id, m1.id)
    production_execution_service.transition_execution(
        db_session, user.id, ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )

    # Attempt to reassign worker via assign_worker
    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_worker(db_session, user.id, ex.id, w2.id)
    assert exc_info.value.code == "REASSIGNMENT_NOT_ALLOWED"
    assert exc_info.value.status_code == 409


def test_j3_32_paused_reassignment_rejected(db_session: Session):
    """Test 32: Reassigning worker or machine while PAUSED is rejected -> 409 REASSIGNMENT_NOT_ALLOWED."""
    user = create_test_user(db_session, "j3_reassign_paused")
    w1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    w2 = Worker(id=uuid.uuid4(), user_id=user.id, name="Sunil Caster", skill="casting")
    m1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([w1, w2, m1])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    ex = production_execution_service.initialize_order_executions(db_session, user.id, order.id)[0]

    production_execution_service.assign_worker(db_session, user.id, ex.id, w1.id)
    production_execution_service.assign_machine(db_session, user.id, ex.id, m1.id)
    production_execution_service.transition_execution(
        db_session, user.id, ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.PAUSED)
    )

    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_worker(db_session, user.id, ex.id, w2.id)
    assert exc_info.value.code == "REASSIGNMENT_NOT_ALLOWED"
    assert exc_info.value.status_code == 409


def test_j3_33_completed_reassignment_rejected(db_session: Session):
    """Test 33: Reassignment on COMPLETED execution is rejected."""
    user = create_test_user(db_session, "j3_reassign_comp")
    w1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    w2 = Worker(id=uuid.uuid4(), user_id=user.id, name="Sunil Caster", skill="casting")
    m1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([w1, w2, m1])
    db_session.commit()

    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    ex = production_execution_service.initialize_order_executions(db_session, user.id, order.id)[0]

    production_execution_service.assign_worker(db_session, user.id, ex.id, w1.id)
    production_execution_service.assign_machine(db_session, user.id, ex.id, m1.id)
    production_execution_service.transition_execution(
        db_session, user.id, ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED)
    )

    with pytest.raises(AppException) as exc_info:
        production_execution_service.assign_worker(db_session, user.id, ex.id, w2.id)
    assert exc_info.value.code == "EXECUTION_ALREADY_COMPLETED"
    assert exc_info.value.status_code == 409


# ==============================================================================
# SECTION H: DIRECT EXECUTION (Tests 34 to 36)
# ==============================================================================

def test_j3_34_direct_execution_respects_worker_validation(client: TestClient, db_session: Session):
    """Test 34: Direct creation validates worker skill -> rejects if ineligible."""
    user = create_test_user(db_session, "j3_dir_w")
    polisher = Worker(id=uuid.uuid4(), user_id=user.id, name="Amit Polisher", skill="polishing")
    db_session.add(polisher)
    db_session.commit()

    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    step = steps[0]  # requires "casting"

    headers = auth_headers(user)
    resp = client.post(
        "/api/v1/production/executions",
        headers=headers,
        json={
            "production_order_id": str(order.id),
            "production_step_id": str(step.id),
            "worker_id": str(polisher.id),
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "WORKER_INELIGIBLE_SKILL"


def test_j3_35_direct_execution_respects_machine_validation(client: TestClient, db_session: Session):
    """Test 35: Direct creation validates machine compatibility -> rejects if incompatible."""
    user = create_test_user(db_session, "j3_dir_m")
    engraver = Machine(id=uuid.uuid4(), user_id=user.id, name="Laser Engraver", machine_type="laser_engraver")
    db_session.add(engraver)
    db_session.commit()

    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    step = steps[0]  # requires "casting_furnace"

    headers = auth_headers(user)
    resp = client.post(
        "/api/v1/production/executions",
        headers=headers,
        json={
            "production_order_id": str(order.id),
            "production_step_id": str(step.id),
            "machine_id": str(engraver.id),
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "MACHINE_INCOMPATIBLE_TYPE"


def test_j3_36_direct_execution_respects_predecessor_rules(client: TestClient, db_session: Session):
    """Test 36: Direct execution of Step 2 starts in PENDING if Step 1 is uncompleted."""
    user = create_test_user(db_session, "j3_dir_pred")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=2)
    step2 = steps[1]

    created = production_execution_service.create_execution(
        db=db_session,
        user_id=user.id,
        create_in=OperationExecutionCreate(
            production_order_id=order.id,
            production_step_id=step2.id,
        ),
    )
    assert created.status == "pending"


# ==============================================================================
# SECTION I: SECURITY & MULTI-TENANT ISOLATION (Tests 37 to 42)
# ==============================================================================

def test_j3_37_cross_tenant_execution_access_rejected(client: TestClient, db_session: Session):
    """Test 37: User B cannot view or transition User A's execution -> 404."""
    user_a = create_test_user(db_session, "j3_sec_a")
    user_b = create_test_user(db_session, "j3_sec_b")

    _, _, _, order_a, _, _ = setup_complete_order_environment(db_session, user_a, num_steps=1)
    ex_a = production_execution_service.initialize_order_executions(db_session, user_a.id, order_a.id)[0]

    headers_b = auth_headers(user_b)
    resp_get = client.get(f"/api/v1/production/executions/{ex_a.id}", headers=headers_b)
    assert resp_get.status_code == 404

    resp_trans = client.post(
        f"/api/v1/production/executions/{ex_a.id}/transition",
        headers=headers_b,
        json={"target_status": "in_progress"},
    )
    assert resp_trans.status_code == 404


def test_j3_38_cross_tenant_worker_assignment_rejected(client: TestClient, db_session: Session):
    """Test 38: User A cannot assign User B's worker via POST /assign-worker -> 404."""
    user_a = create_test_user(db_session, "j3_sec_wa")
    user_b = create_test_user(db_session, "j3_sec_wb")

    worker_b = Worker(id=uuid.uuid4(), user_id=user_b.id, name="Secret Worker", skill="casting")
    db_session.add(worker_b)
    db_session.commit()

    _, _, _, order_a, _, _ = setup_complete_order_environment(db_session, user_a, num_steps=1)
    ex_a = production_execution_service.initialize_order_executions(db_session, user_a.id, order_a.id)[0]

    headers_a = auth_headers(user_a)
    resp = client.post(
        f"/api/v1/production/executions/{ex_a.id}/assign-worker",
        headers=headers_a,
        json={"worker_id": str(worker_b.id)},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "WORKER_NOT_FOUND"


def test_j3_39_cross_tenant_machine_assignment_rejected(client: TestClient, db_session: Session):
    """Test 39: User A cannot assign User B's machine via POST /assign-machine -> 404."""
    user_a = create_test_user(db_session, "j3_sec_ma")
    user_b = create_test_user(db_session, "j3_sec_mb")

    machine_b = Machine(id=uuid.uuid4(), user_id=user_b.id, name="Secret Furnace", machine_type="casting_furnace")
    db_session.add(machine_b)
    db_session.commit()

    _, _, _, order_a, _, _ = setup_complete_order_environment(db_session, user_a, num_steps=1)
    ex_a = production_execution_service.initialize_order_executions(db_session, user_a.id, order_a.id)[0]

    headers_a = auth_headers(user_a)
    resp = client.post(
        f"/api/v1/production/executions/{ex_a.id}/assign-machine",
        headers=headers_a,
        json={"machine_id": str(machine_b.id)},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "MACHINE_NOT_FOUND"


def test_j3_40_client_user_id_injection_rejected(client: TestClient, db_session: Session):
    """Test 40: Injecting user_id in assign-worker, assign-machine, or transition fails with 422."""
    user = create_test_user(db_session, "j3_inject_uid")
    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    ex = production_execution_service.initialize_order_executions(db_session, user.id, order.id)[0]
    headers = auth_headers(user)

    # Extra field injection
    resp_w = client.post(
        f"/api/v1/production/executions/{ex.id}/assign-worker",
        headers=headers,
        json={"worker_id": str(uuid.uuid4()), "user_id": str(uuid.uuid4())},
    )
    assert resp_w.status_code == 422

    resp_m = client.post(
        f"/api/v1/production/executions/{ex.id}/assign-machine",
        headers=headers,
        json={"machine_id": str(uuid.uuid4()), "user_id": str(uuid.uuid4())},
    )
    assert resp_m.status_code == 422


def test_j3_41_client_status_injection_rejected(client: TestClient, db_session: Session):
    """Test 41: Direct execution creation cannot inject arbitrary status (e.g. status='completed')."""
    user = create_test_user(db_session, "j3_inject_status")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    headers = auth_headers(user)

    resp = client.post(
        "/api/v1/production/executions",
        headers=headers,
        json={
            "production_order_id": str(order.id),
            "production_step_id": str(steps[0].id),
            "status": "completed",
        },
    )
    assert resp.status_code == 422


def test_j3_42_client_timestamp_injection_rejected(client: TestClient, db_session: Session):
    """Test 42: Client cannot inject actual_start_time or completed_at in transition payload."""
    user = create_test_user(db_session, "j3_inject_ts")
    _, _, _, order, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    ex = production_execution_service.initialize_order_executions(db_session, user.id, order.id)[0]
    headers = auth_headers(user)

    resp = client.post(
        f"/api/v1/production/executions/{ex.id}/transition",
        headers=headers,
        json={
            "target_status": "in_progress",
            "actual_start_time": "2025-01-01T00:00:00Z",
            "completed_at": "2025-01-01T01:00:00Z",
        },
    )
    assert resp.status_code == 422


# ==============================================================================
# SECTION J: CONCURRENCY & PLANNED VS ACTUAL (Tests 43 to 45)
# ==============================================================================

def test_j3_43_two_operations_cannot_reserve_same_worker_simultaneously(db_session: Session):
    """Test 43: Double-booking prevention: starting two operations on the same worker is prevented."""
    user = create_test_user(db_session, "j3_race_w")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Goldsmith", skill="casting")
    m1 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    m2 = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Beta", machine_type="casting_furnace")
    db_session.add_all([worker, m1, m2])
    db_session.commit()

    _, _, _, order1, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    _, _, _, order2, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    op_a = production_execution_service.initialize_order_executions(db_session, user.id, order1.id)[0]
    op_b = production_execution_service.initialize_order_executions(db_session, user.id, order2.id)[0]

    production_execution_service.assign_worker(db_session, user.id, op_a.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, op_a.id, m1.id)
    production_execution_service.assign_worker(db_session, user.id, op_b.id, worker.id)
    production_execution_service.assign_machine(db_session, user.id, op_b.id, m2.id)

    # First operation starts
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )

    # Second operation cannot start concurrently
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db=db_session,
            user_id=user.id,
            execution_id=op_b.id,
            req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "WORKER_RESOURCE_CONFLICT"
    assert exc_info.value.status_code == 409


def test_j3_44_two_operations_cannot_reserve_same_machine_simultaneously(db_session: Session):
    """Test 44: Double-booking prevention: starting two operations on the same machine is prevented."""
    user = create_test_user(db_session, "j3_race_m")
    w1 = Worker(id=uuid.uuid4(), user_id=user.id, name="Rahul Caster", skill="casting")
    w2 = Worker(id=uuid.uuid4(), user_id=user.id, name="Sunil Caster", skill="casting")
    furnace = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([w1, w2, furnace])
    db_session.commit()

    _, _, _, order1, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    _, _, _, order2, _, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    op_a = production_execution_service.initialize_order_executions(db_session, user.id, order1.id)[0]
    op_b = production_execution_service.initialize_order_executions(db_session, user.id, order2.id)[0]

    production_execution_service.assign_worker(db_session, user.id, op_a.id, w1.id)
    production_execution_service.assign_machine(db_session, user.id, op_a.id, furnace.id)
    production_execution_service.assign_worker(db_session, user.id, op_b.id, w2.id)
    production_execution_service.assign_machine(db_session, user.id, op_b.id, furnace.id)

    # First operation starts
    production_execution_service.transition_execution(
        db_session, user.id, op_a.id, OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS)
    )

    # Second operation cannot start concurrently with same machine
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db=db_session,
            user_id=user.id,
            execution_id=op_b.id,
            req=OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "MACHINE_RESOURCE_CONFLICT"
    assert exc_info.value.status_code == 409


def test_j3_45_planned_vs_actual_resource_preservation(client: TestClient, db_session: Session):
    """Test 45: Preserves CP-SAT planned worker/machine while recording actual execution worker/machine."""
    user = create_test_user(db_session, "j3_plan_vs_act")
    w_planned = Worker(id=uuid.uuid4(), user_id=user.id, name="Planned Caster", skill="casting")
    m_planned = Machine(id=uuid.uuid4(), user_id=user.id, name="Planned Furnace", machine_type="casting_furnace")
    w_actual = Worker(id=uuid.uuid4(), user_id=user.id, name="Actual Caster", skill="casting")
    m_actual = Machine(id=uuid.uuid4(), user_id=user.id, name="Actual Furnace", machine_type="casting_furnace")
    db_session.add_all([w_planned, m_planned, w_actual, m_actual])
    db_session.commit()

    _, _, _, order, steps, tasks = setup_complete_order_environment(db_session, user, num_steps=1, with_schedule=True)
    task = tasks[0]
    task.worker_id = w_planned.id
    task.machine_id = m_planned.id
    db_session.commit()

    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    # Assign different ACTUAL worker and machine
    production_execution_service.assign_worker(db_session, user.id, ex.id, w_actual.id)
    production_execution_service.assign_machine(db_session, user.id, ex.id, m_actual.id)

    # Verify via API response
    headers = auth_headers(user)
    resp = client.get(f"/api/v1/production/executions/{ex.id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # ScheduledTask plan is untouched
    assert data["planned_worker_id"] == str(w_planned.id)
    assert data["planned_worker_name"] == "Planned Caster"
    assert data["planned_machine_id"] == str(m_planned.id)
    assert data["planned_machine_name"] == "Planned Furnace"

    # OperationExecution actual reality is recorded
    assert data["actual_worker_id"] == str(w_actual.id)
    assert data["worker_name"] == "Actual Caster"
    assert data["actual_machine_id"] == str(m_actual.id)
    assert data["machine_name"] == "Actual Furnace"
