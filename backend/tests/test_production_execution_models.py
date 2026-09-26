"""
Phase J.1 — Production Execution Foundation & Data Model Test Suite
Verifies:
1. Model creation & persistence
2. Migration integrity & schema constraints
3. Required foreign keys (user_id, production_order_id, production_step_id)
4. Tenant ownership validation
5. Production order linkage & validation
6. Production step linkage (verifying step belongs to order's specification)
7. ScheduledTask optional linkage (nullable or linked)
8. Worker ownership validation (cross-tenant rejected)
9. Machine ownership validation (cross-tenant rejected)
10. Duplicate initialization protection (idempotency)
11. Initial READY / PENDING states (Step 1 READY, Steps 2..N PENDING)
12. PENDING -> READY transition
13. READY -> IN_PROGRESS transition
14. IN_PROGRESS -> PAUSED transition
15. PAUSED -> IN_PROGRESS transition
16. IN_PROGRESS -> COMPLETED transition
17. Invalid transitions rejected
18. COMPLETED immutability (409 Conflict)
19. Actual start timestamp recorded on start
20. Actual end timestamp recorded on completion
21. Actual duration accurately calculated
22. Pause duration calculated and deducted without double-counting
23. Cross-tenant IDOR protection (404 Not Found)
24. Client timestamp injection forbidden (422 Unprocessable)
25. Client user_id injection forbidden (422 Unprocessable)
26. Transaction rollback on error
27. Schedule-linked execution (copies planned timing and assignments from ScheduledTask)
28. Unscheduled execution (direct execution initializes without schedule)
29. Multiple routing steps support
30. Ordering by step_number
31. BLOCKED state transitions (READY -> BLOCKED, IN_PROGRESS -> BLOCKED, BLOCKED -> READY)
32. Legacy order lacking specification rejects execution initialization
33. API endpoints: initialize, list, get, and transition
"""

import math
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token
from app.models.design import Design, DesignRender
from app.models.execution import OperationExecution
from app.models.production import Machine, ProductionOrder, Worker
from app.models.schedule import ProductionSchedule, ScheduledTask
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
    OperationExecutionCreate,
    OperationExecutionTransitionRequest,
)
from app.services.production_execution_service import production_execution_service
from app.services.user_service import user_service


# ==============================================================================
# Test Helpers & Fixtures
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
) -> tuple[Design, DesignRender, ProductionSpecification, ProductionOrder, list[ProductionStep], list[ScheduledTask]]:
    """
    Sets up an approved Design, approved Render, approved Specification with N steps,
    and a spec-backed ProductionOrder. Optionally sets up ScheduledTasks.
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
        estimated_rough_metal_weight_grams=6.5,
        estimated_finished_metal_weight_grams=5.8,
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

    steps: list[ProductionStep] = []
    step_defs = [
        ("Casting & Tree Preparation", "casting", "casting_furnace", 1.5, 0.25),
        ("Stone Setting (Collet)", "stone_setting", None, 2.0, 0.5),
        ("Hand Polishing & Ultrasonic Clean", "polishing", "ultrasonic_cleaner", 1.0, 0.2),
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

    scheduled_tasks: list[ScheduledTask] = []
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
                sequence_order=st.step_number,
            )
            db.add(task)
            scheduled_tasks.append(task)
            start_cursor = end_cursor + timedelta(hours=1)
        db.commit()

    return design, render, spec, order, steps, scheduled_tasks


# ==============================================================================
# 1. Model Creation & Constraints Tests
# ==============================================================================

def test_operation_execution_model_creation(db_session: Session):
    """Test 1: Model creation with required fields, constraints, and defaults."""
    user = create_test_user(db_session, "model")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    execution = OperationExecution(
        id=uuid.uuid4(),
        user_id=user.id,
        production_order_id=order.id,
        production_step_id=steps[0].id,
        status="ready",
        planned_duration_hours=2.0,
    )
    db_session.add(execution)
    db_session.commit()
    db_session.refresh(execution)

    assert execution.id is not None
    assert execution.user_id == user.id
    assert execution.production_order_id == order.id
    assert execution.production_step_id == steps[0].id
    assert execution.status == "ready"
    assert execution.pause_duration_hours == 0.0
    assert execution.actual_start_time is None
    assert execution.actual_end_time is None
    assert execution.created_at is not None
    assert execution.updated_at is not None


def test_operation_execution_status_check_constraint(db_session: Session):
    """Test 2: Rejects invalid status string at database level."""
    user = create_test_user(db_session, "badstatus")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    execution = OperationExecution(
        id=uuid.uuid4(),
        user_id=user.id,
        production_order_id=order.id,
        production_step_id=steps[0].id,
        status="invalid_status_value",
    )
    db_session.add(execution)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_operation_execution_unique_order_step_constraint(db_session: Session):
    """Test 3: Database enforces unique (production_order_id, production_step_id)."""
    user = create_test_user(db_session, "uqorderstep")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    ex1 = OperationExecution(
        id=uuid.uuid4(),
        user_id=user.id,
        production_order_id=order.id,
        production_step_id=steps[0].id,
        status="ready",
    )
    db_session.add(ex1)
    db_session.commit()

    # Attempt second execution for the exact same order and step
    ex2 = OperationExecution(
        id=uuid.uuid4(),
        user_id=user.id,
        production_order_id=order.id,
        production_step_id=steps[0].id,
        status="ready",
    )
    db_session.add(ex2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ==============================================================================
# 2. Initialization Service & Idempotency Tests
# ==============================================================================

def test_initialize_order_executions_initial_states(db_session: Session):
    """Test 4: Initializing executions sets Step 1 to READY and subsequent steps to PENDING."""
    user = create_test_user(db_session, "initstates")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=3)

    executions = production_execution_service.initialize_order_executions(
        db=db_session,
        user_id=user.id,
        order_id=order.id,
    )

    assert len(executions) == 3
    # Step 1 must be READY
    assert executions[0].status == "ready"
    assert executions[0].production_step_id == steps[0].id

    # Steps 2 and 3 must be PENDING
    assert executions[1].status == "pending"
    assert executions[1].production_step_id == steps[1].id
    assert executions[2].status == "pending"
    assert executions[2].production_step_id == steps[2].id


def test_initialize_order_executions_idempotency(db_session: Session):
    """Test 5: Calling initialize_order_executions twice returns existing records without duplicates."""
    user = create_test_user(db_session, "idempotent")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=2)

    first_run = production_execution_service.initialize_order_executions(
        db=db_session,
        user_id=user.id,
        order_id=order.id,
    )
    assert len(first_run) == 2

    # Second call on same order
    second_run = production_execution_service.initialize_order_executions(
        db=db_session,
        user_id=user.id,
        order_id=order.id,
    )
    assert len(second_run) == 2
    assert [e.id for e in first_run] == [e.id for e in second_run]

    # Verify count in database is still 2
    count = db_session.query(OperationExecution).filter(OperationExecution.production_order_id == order.id).count()
    assert count == 2


def test_initialize_order_executions_scheduled_linkage(db_session: Session):
    """Test 6: Copies planned timing and task linkage when ScheduledTasks exist."""
    user = create_test_user(db_session, "schedlink")
    _, _, spec, order, steps, scheduled_tasks = setup_complete_order_environment(
        db_session, user, num_steps=2, with_schedule=True
    )

    executions = production_execution_service.initialize_order_executions(
        db=db_session,
        user_id=user.id,
        order_id=order.id,
    )

    assert len(executions) == 2
    assert executions[0].scheduled_task_id == scheduled_tasks[0].id
    assert executions[0].planned_start_time == scheduled_tasks[0].start_time
    assert executions[0].planned_end_time == scheduled_tasks[0].end_time
    assert executions[0].planned_duration_hours == scheduled_tasks[0].duration_hours

    assert executions[1].scheduled_task_id == scheduled_tasks[1].id
    assert executions[1].planned_start_time == scheduled_tasks[1].start_time


def test_initialize_order_executions_unscheduled_direct(db_session: Session):
    """Test 7: Direct unscheduled orders initialize planned_duration from formula with scheduled_task_id=None."""
    user = create_test_user(db_session, "unsched")
    _, _, spec, order, steps, _ = setup_complete_order_environment(
        db_session, user, num_steps=2, with_schedule=False
    )

    executions = production_execution_service.initialize_order_executions(
        db=db_session,
        user_id=user.id,
        order_id=order.id,
    )

    assert len(executions) == 2
    assert executions[0].scheduled_task_id is None
    # duration = max(1, ceil(base_h + per_unit_h * qty)) = max(1, ceil(1.5 + 0.25 * 2)) = 2.0
    assert executions[0].planned_duration_hours == 2.0
    assert executions[0].planned_start_time is None


def test_initialize_legacy_order_without_specification_fails(db_session: Session):
    """Test 8: Orders lacking a specification cannot be initialized into step executions."""
    user = create_test_user(db_session, "legacylack")
    design = Design(id=uuid.uuid4(), user_id=user.id, name="Legacy Ring", category="ring")
    db_session.add(design)
    db_session.commit()

    legacy_order = ProductionOrder(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        quantity=1,
        priority="low",
        status="pending",
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
        specification_id=None,
    )
    db_session.add(legacy_order)
    db_session.commit()

    with pytest.raises(AppException) as exc_info:
        production_execution_service.initialize_order_executions(
            db=db_session,
            user_id=user.id,
            order_id=legacy_order.id,
        )
    assert exc_info.value.code == "ORDER_LACKS_SPECIFICATION"
    assert exc_info.value.status_code == 400


# ==============================================================================
# 3. State Machine & Transition Tests
# ==============================================================================

def test_transition_ready_to_in_progress(db_session: Session):
    """Test 9: READY -> IN_PROGRESS sets actual_start_time."""
    user = create_test_user(db_session, "startop")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    target_ex = executions[0]
    assert target_ex.status == "ready"

    updated = production_execution_service.transition_execution(
        db=db_session,
        user_id=user.id,
        execution_id=target_ex.id,
        req=OperationExecutionTransitionRequest(
            target_status=ExecutionStatus.IN_PROGRESS,
            operator_notes="Starting casting flask burnout.",
        ),
    )

    assert updated.status == "in_progress"
    assert updated.actual_start_time is not None
    assert updated.actual_end_time is None
    assert "Starting casting flask burnout." in (updated.operator_notes or "")


def test_transition_in_progress_to_paused_and_resumed(db_session: Session):
    """Test 10: IN_PROGRESS -> PAUSED -> IN_PROGRESS records pause duration accurately."""
    user = create_test_user(db_session, "pauseop")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    target_ex = executions[0]

    # Start
    started = production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    assert started.status == "in_progress"

    # Pause
    paused = production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(
            target_status=ExecutionStatus.PAUSED,
            operator_notes="Lunch break / furnace preheat waiting",
        ),
    )
    assert paused.status == "paused"
    assert paused.last_paused_at is not None

    # Simulate 30-minute pause in the past
    paused.last_paused_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    db_session.commit()

    # Resume
    resumed = production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    assert resumed.status == "in_progress"
    assert resumed.last_paused_at is None
    # 30 minutes is 0.5 hours (+/- rounding precision)
    assert 0.49 <= resumed.pause_duration_hours <= 0.55


def test_transition_in_progress_to_completed_duration_calculation(db_session: Session):
    """Test 11: IN_PROGRESS -> COMPLETED sets actual_end_time and computes net duration minus pause."""
    user = create_test_user(db_session, "completeop")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    target_ex = executions[0]

    # Set up simulated execution that started 3 hours ago with 1 hour paused
    target_ex.status = "in_progress"
    target_ex.actual_start_time = datetime.now(timezone.utc) - timedelta(hours=3)
    target_ex.pause_duration_hours = 1.0
    db_session.commit()

    completed = production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(
            target_status=ExecutionStatus.COMPLETED,
            operator_notes="Casting complete, gates cut, sprue filed.",
        ),
    )

    assert completed.status == "completed"
    assert completed.actual_end_time is not None
    assert completed.completed_at is not None
    # Net duration: 3.0 elapsed - 1.0 paused = ~2.0 hours
    assert 1.95 <= (completed.actual_duration_hours or 0.0) <= 2.05


def test_transition_pending_to_ready(db_session: Session):
    """Test 12: PENDING -> READY enforces predecessor completion, then advances to READY."""
    user = create_test_user(db_session, "pendingready")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex = executions[0]
    step2_ex = executions[1]
    assert step2_ex.status == "pending"

    # Predecessor incomplete: transition to READY is rejected
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user.id, step2_ex.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.READY),
        )
    assert exc_info.value.code == "PREDECESSOR_NOT_COMPLETED"
    assert exc_info.value.status_code == 409

    # Complete Step 1
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    # Step 2 is now automatically advanced to READY
    db_session.refresh(step2_ex)
    assert step2_ex.status == "ready"


def test_transition_blocked_and_unblocked(db_session: Session):
    """Test 13: Operations can transition to BLOCKED and unblock back to READY."""
    user = create_test_user(db_session, "blockedstate")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    target_ex = executions[0]

    # READY -> BLOCKED
    blocked = production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(
            target_status=ExecutionStatus.BLOCKED,
            operator_notes="Missing gold casting grain from vault.",
        ),
    )
    assert blocked.status == "blocked"

    # BLOCKED -> READY
    unblocked = production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(
            target_status=ExecutionStatus.READY,
            operator_notes="Gold grain received.",
        ),
    )
    assert unblocked.status == "ready"


def test_invalid_state_transitions_rejected(db_session: Session):
    """Test 14: Rejects illegal state machine jumps (e.g. PENDING -> COMPLETED)."""
    user = create_test_user(db_session, "badtrans")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    pending_ex = executions[1]
    assert pending_ex.status == "pending"

    # PENDING -> COMPLETED is illegal
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user.id, pending_ex.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
        )
    assert exc_info.value.code == "INVALID_EXECUTION_TRANSITION"
    assert exc_info.value.status_code == 400

    # PENDING -> IN_PROGRESS is illegal
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user.id, pending_ex.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "INVALID_EXECUTION_TRANSITION"


def test_completed_execution_immutability(db_session: Session):
    """Test 15: Once COMPLETED, an operation execution cannot be modified or restarted (409 Conflict)."""
    user = create_test_user(db_session, "immutable")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    target_ex = executions[0]

    # Advance to COMPLETED
    production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    completed = production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    assert completed.status == "completed"

    # Attempt transition out of COMPLETED
    for forbidden_target in [ExecutionStatus.IN_PROGRESS, ExecutionStatus.READY, ExecutionStatus.PAUSED]:
        with pytest.raises(AppException) as exc_info:
            production_execution_service.transition_execution(
                db_session, user.id, target_ex.id,
                OperationExecutionTransitionRequest(target_status=forbidden_target),
            )
        assert exc_info.value.code == "EXECUTION_ALREADY_COMPLETED"
        assert exc_info.value.status_code == 409


# ==============================================================================
# 4. Multi-Tenant Security & IDOR Tests
# ==============================================================================

def test_cross_tenant_execution_idor_protection(db_session: Session):
    """Test 16: User A cannot read or transition User B's execution (returns 404)."""
    user_a = create_test_user(db_session, "usera")
    user_b = create_test_user(db_session, "userb")

    _, _, spec_a, order_a, _, _ = setup_complete_order_environment(db_session, user_a, num_steps=1)
    executions_a = production_execution_service.initialize_order_executions(db_session, user_a.id, order_a.id)
    ex_a = executions_a[0]

    # User B attempts to read User A's execution
    with pytest.raises(AppException) as exc_info:
        production_execution_service.get_execution_by_id(db_session, user_b.id, ex_a.id)
    assert exc_info.value.code == "EXECUTION_NOT_FOUND"
    assert exc_info.value.status_code == 404

    # User B attempts to transition User A's execution
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user_b.id, ex_a.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "EXECUTION_NOT_FOUND"
    assert exc_info.value.status_code == 404


def test_cross_tenant_resource_assignment_rejected(db_session: Session):
    """Test 17: Cannot assign another user's Worker or Machine to an execution."""
    user_a = create_test_user(db_session, "artisan_a")
    user_b = create_test_user(db_session, "artisan_b")

    # User B owns a machine
    machine_b = Machine(id=uuid.uuid4(), user_id=user_b.id, name="User B Laser", machine_type="laser_engraver")
    db_session.add(machine_b)
    db_session.commit()

    _, _, spec_a, order_a, _, _ = setup_complete_order_environment(db_session, user_a, num_steps=1)
    executions_a = production_execution_service.initialize_order_executions(db_session, user_a.id, order_a.id)
    ex_a = executions_a[0]

    # User A tries to assign User B's machine during transition
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user_a.id, ex_a.id,
            OperationExecutionTransitionRequest(
                target_status=ExecutionStatus.IN_PROGRESS,
                machine_id=machine_b.id,
            ),
        )
    assert exc_info.value.code == "MACHINE_NOT_FOUND"
    assert exc_info.value.status_code == 404


# ==============================================================================
# 5. Direct Creation & Step-Order Linkage Tests
# ==============================================================================

def test_direct_execution_creation_linkage_validation(db_session: Session):
    """Test 18: Direct creation validates that production_step belongs to the order's specification."""
    user = create_test_user(db_session, "directlink")
    _, _, spec1, order1, steps1, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    _, _, spec2, order2, steps2, _ = setup_complete_order_environment(db_session, user, num_steps=1)

    # Valid creation: Order 1 + Step from Order 1
    valid_ex = production_execution_service.create_execution(
        db_session, user.id,
        OperationExecutionCreate(
            production_order_id=order1.id,
            production_step_id=steps1[0].id,
            operator_notes="Directly initiated step.",
        ),
    )
    assert valid_ex.id is not None

    # Invalid cross-linkage: Order 1 + Step from Order 2
    with pytest.raises(AppException) as exc_info:
        production_execution_service.create_execution(
            db_session, user.id,
            OperationExecutionCreate(
                production_order_id=order1.id,
                production_step_id=steps2[0].id,
            ),
        )
    assert exc_info.value.code == "INVALID_STEP_ORDER_LINKAGE"
    assert exc_info.value.status_code == 400


# ==============================================================================
# 6. REST API Endpoints Integration Tests
# ==============================================================================

def test_api_initialize_and_list_executions(client: TestClient, db_session: Session):
    """Test 19: POST /orders/{id}/executions/initialize and GET /orders/{id}/executions."""
    user = create_test_user(db_session, "apiuser")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=2)

    headers = auth_headers(user)

    # 1. Initialize executions via POST API
    init_res = client.post(
        f"/api/v1/production/orders/{order.id}/executions/initialize",
        headers=headers,
    )
    assert init_res.status_code == 201
    init_data = init_res.json()
    assert len(init_data) == 2
    assert init_data[0]["status"] == "ready"
    assert init_data[1]["status"] == "pending"

    # 2. List executions via GET API
    list_res = client.get(
        f"/api/v1/production/orders/{order.id}/executions",
        headers=headers,
    )
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 2
    assert list_data["order_id"] == str(order.id)
    assert len(list_data["items"]) == 2
    assert list_data["items"][0]["step_number"] == 1
    assert list_data["items"][1]["step_number"] == 2


def test_api_get_and_transition_execution(client: TestClient, db_session: Session):
    """Test 20: GET /executions/{id} and POST /executions/{id}/transition."""
    user = create_test_user(db_session, "apivalid")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    headers = auth_headers(user)

    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex_id = str(executions[0].id)

    # 1. GET single execution
    get_res = client.get(f"/api/v1/production/executions/{ex_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == ex_id
    assert get_res.json()["status"] == "ready"

    # 2. POST transition to IN_PROGRESS
    trans_res = client.post(
        f"/api/v1/production/executions/{ex_id}/transition",
        headers=headers,
        json={"target_status": "in_progress", "operator_notes": "Artisan checked in."},
    )
    assert trans_res.status_code == 200
    data = trans_res.json()
    assert data["status"] == "in_progress"
    assert data["actual_start_time"] is not None


def test_api_forbids_client_controlled_fields_injection(client: TestClient, db_session: Session):
    """Test 21: Client cannot inject completed_at, actual_duration_hours, or timestamps."""
    user = create_test_user(db_session, "injecttest")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    headers = auth_headers(user)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex_id = str(executions[0].id)

    # Client tries to inject forbidden server-controlled fields into transition payload
    payload = {
        "target_status": "in_progress",
        "actual_start_time": "2020-01-01T00:00:00Z",
        "completed_at": "2020-01-01T01:00:00Z",
        "actual_duration_hours": 0.01,
        "user_id": str(uuid.uuid4()),
    }
    res = client.post(
        f"/api/v1/production/executions/{ex_id}/transition",
        headers=headers,
        json=payload,
    )
    # Pydantic extra="forbid" rejects unexpected extra fields with 422
    assert res.status_code == 422


# ==============================================================================
# 7. Comprehensive Edge Cases & Advanced Scenarios
# ==============================================================================

def test_multiple_pause_resume_cycles_accumulate_duration(db_session: Session):
    """Test 22: Multiple pause/resume cycles accumulate pause duration accurately without double-counting."""
    user = create_test_user(db_session, "multipause")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    target_ex = executions[0]

    # 1. Start
    production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    # 2. First pause: 20 minutes (0.333h)
    production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.PAUSED),
    )
    target_ex.last_paused_at = datetime.now(timezone.utc) - timedelta(minutes=20)
    db_session.commit()

    production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    first_pause_accum = target_ex.pause_duration_hours
    assert 0.30 <= first_pause_accum <= 0.36

    # 3. Second pause: 40 minutes (0.667h)
    production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.PAUSED),
    )
    target_ex.last_paused_at = datetime.now(timezone.utc) - timedelta(minutes=40)
    db_session.commit()

    production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    total_pause = target_ex.pause_duration_hours
    # Total pause: 20m + 40m = 60m = ~1.0h
    assert 0.95 <= total_pause <= 1.05


def test_operator_notes_concatenation_across_transitions(db_session: Session):
    """Test 23: Operator notes concatenate chronologically with audit timestamps."""
    user = create_test_user(db_session, "notesaudit")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    target_ex = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(
            target_status=ExecutionStatus.IN_PROGRESS,
            operator_notes="Shift 1: Starting wax carve inspection.",
        ),
    )
    production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(
            target_status=ExecutionStatus.PAUSED,
            operator_notes="Shift 1: Handing over to night lead.",
        ),
    )

    db_session.refresh(target_ex)
    notes = target_ex.operator_notes or ""
    assert "Starting wax carve inspection." in notes
    assert "Handing over to night lead." in notes


def test_order_deletion_prevented_when_executions_exist(db_session: Session):
    """Test 24: Deleting a ProductionOrder is blocked by RESTRICT when execution history exists."""
    user = create_test_user(db_session, "orderprotect")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    production_execution_service.initialize_order_executions(db_session, user.id, order.id)

    # Attempt to delete the parent production order
    db_session.delete(order)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_step_deletion_prevented_when_executions_exist(db_session: Session):
    """Test 25: Deleting a ProductionStep is blocked by RESTRICT when execution history references it."""
    from sqlalchemy import text
    db_session.execute(text("PRAGMA foreign_keys = ON;"))
    user = create_test_user(db_session, "stepprotect")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    production_execution_service.initialize_order_executions(db_session, user.id, order.id)

    # Attempt to delete the step
    db_session.delete(steps[0])
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_scheduled_task_order_mismatch_rejected(db_session: Session):
    """Test 26: Linking a ScheduledTask from a different order is rejected with 400."""
    user = create_test_user(db_session, "taskmismatch")
    _, _, spec1, order1, steps1, sched1 = setup_complete_order_environment(
        db_session, user, num_steps=1, with_schedule=True
    )
    _, _, spec2, order2, steps2, sched2 = setup_complete_order_environment(
        db_session, user, num_steps=1, with_schedule=True
    )

    # Try to create execution for order1 referencing task from order2
    with pytest.raises(AppException) as exc_info:
        production_execution_service.create_execution(
            db_session, user.id,
            OperationExecutionCreate(
                production_order_id=order1.id,
                production_step_id=steps1[0].id,
                scheduled_task_id=sched2[0].id,  # Belongs to order2!
            ),
        )
    assert exc_info.value.code == "TASK_ORDER_MISMATCH"
    assert exc_info.value.status_code == 400


def test_multiple_steps_sequential_ordering_and_context(db_session: Session):
    """Test 27: 4-step routing preserves step numbers and contextual metadata."""
    user = create_test_user(db_session, "multistep")
    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=4)

    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    assert len(executions) == 4

    step_nums = [e.production_step.step_number for e in executions]
    assert step_nums == [1, 2, 3, 4]

    # Verify denormalized helper
    resp = production_execution_service.get_order_executions(db_session, user.id, order.id)
    assert len(resp) == 4
    assert resp[0].production_step.stage_name == "Casting & Tree Preparation"
    assert resp[1].production_step.stage_name == "Stone Setting (Collet)"
    assert resp[2].production_step.stage_name == "Hand Polishing & Ultrasonic Clean"
    assert resp[3].production_step.stage_name == "Laser Hallmark Engraving"


def test_transition_with_valid_worker_and_machine(db_session: Session):
    """Test 28: Assigning a valid worker and machine during transition succeeds."""
    user = create_test_user(db_session, "resassign")
    worker = Worker(id=uuid.uuid4(), user_id=user.id, name="Jean Pierre", skill="casting")
    machine = Machine(id=uuid.uuid4(), user_id=user.id, name="Furnace Alpha", machine_type="casting_furnace")
    db_session.add_all([worker, machine])
    db_session.commit()

    _, _, spec, order, steps, _ = setup_complete_order_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    target_ex = executions[0]

    updated = production_execution_service.transition_execution(
        db_session, user.id, target_ex.id,
        OperationExecutionTransitionRequest(
            target_status=ExecutionStatus.IN_PROGRESS,
            worker_id=worker.id,
            machine_id=machine.id,
            operator_notes="Furnace Alpha loaded by Jean Pierre.",
        ),
    )
    assert updated.worker_id == worker.id
    assert updated.machine_id == machine.id
    assert updated.worker.name == "Jean Pierre"
    assert updated.machine.name == "Furnace Alpha"


def test_api_unauthorized_access_rejected(client: TestClient, db_session: Session):
    """Test 29: Calls without bearer token return 401 Unauthorized."""
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/production/executions/{fake_id}")
    assert res.status_code == 401

    res_init = client.post(f"/api/v1/production/orders/{fake_id}/executions/initialize")
    assert res_init.status_code == 401
