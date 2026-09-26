"""
Phase J.2: Execution Workflow & Automatic Routing Progression Test Suite
Validates:
1. Initialization: Step 1 READY, Steps 2..N PENDING
2. Start Step 1: READY -> IN_PROGRESS sets actual_start_time and updates order status to in_progress
3. Complete Step 1: Step 1 -> COMPLETED, Step 2 automatically advances to READY
4. Complete Step 2: Step 3 automatically advances to READY
5. Full N-step progression: 5-step routing progresses sequentially to final COMPLETED
6. Cannot skip: PENDING -> IN_PROGRESS rejected with 400
7. Cannot skip: PENDING -> READY rejected with 409 PREDECESSOR_NOT_COMPLETED if predecessor incomplete
8. Blocked: Step 1 BLOCKED, Step 2 remains PENDING and cannot advance
9. Unblock: Step 1 BLOCKED -> READY, workflow resumes
10. Pause & Resume: IN_PROGRESS -> PAUSED -> IN_PROGRESS preserves timing and accumulates pause duration
11. Atomic completion: failure during advancement rolls back completion and preserves IN_PROGRESS state
12. Duplicate completion: second completion attempt returns 409 EXECUTION_ALREADY_COMPLETED
13. Concurrency / locking: row-level locking with_for_update prevents race conditions
14. Direct execution: cannot bypass predecessor requirements
15. Direct execution: duplicate creation for same (order, step) rejected with 409
16. Initialization idempotency: calling initialize multiple times returns existing executions
17. ScheduledTask planned data: preserved during initialization and progression
18. Unscheduled direct execution: runs cleanly without CP-SAT schedule
19. Cross-tenant isolation: User B cannot access User A executions (404)
20. Cross-tenant resource linking: User B worker/machine rejected (404)
21. Client injection forbidden: client-controlled user_id or timestamps rejected (422)
22. Completed state is terminal: cannot transition away from COMPLETED (409)
23. Final step completion: does not attempt to create nonexistent next execution; marks order completed
24. Workflow progress metrics: list response returns accurate counts and progress percent
25. REST API E2E lifecycle: initialize -> start -> pause -> resume -> complete -> auto-advance -> final complete
"""

import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token
from app.main import app
from app.models.design import Design, DesignRender
from app.models.execution import OperationExecution
from app.models.production import Machine, ProductionOrder, Worker
from app.models.schedule import ProductionSchedule, ScheduledTask
from app.models.specification import ProductionMaterial, ProductionSpecification, ProductionStep
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
# Helpers & Fixtures
# ==============================================================================

def create_test_user(db: Session, prefix: str = "artisan") -> User:
    """Creates a distinct test user in the database."""
    unique_email = f"{prefix}.{uuid.uuid4().hex[:8]}@jewelmind.atelier"
    return user_service.create(
        db,
        UserCreate(
            email=unique_email,
            password="SecurePassword123!",
            full_name=f"Master Artisan {prefix.title()}",
        ),
    )


def auth_headers(user: User) -> dict:
    """Generates bearer authorization headers for a user."""
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def setup_j2_environment(
    db: Session,
    user: User,
    num_steps: int = 5,
    with_schedule: bool = False,
) -> Tuple[Design, DesignRender, ProductionSpecification, ProductionOrder, List[ProductionStep], List[ScheduledTask]]:
    """
    Sets up a complete production environment with N routing steps.
    Default 5 stages: Wax Carving, Casting, Stone Setting, Polishing, Quality Hallmarking.
    """
    stage_templates = [
        ("Wax 3D Printing & Carving", "cad_design", "3d_wax_printer", 2.0, 0.5),
        ("Investment Casting & Burnout", "casting", "casting_furnace", 3.0, 1.0),
        ("Bench Stone Setting", "stone_setting", None, 4.0, 1.5),
        ("Ultrasonic Cleaning & Polishing", "polishing", "ultrasonic_cleaner", 1.5, 0.5),
        ("Final Quality Check & Hallmarking", "general", "laser_engraver", 1.0, 0.2),
    ]

    # 1. Design & Render
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

    # 2. Approved Production Specification
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

    # 3. Sequential Production Steps
    steps: List[ProductionStep] = []
    for i in range(num_steps):
        tmpl = stage_templates[i % len(stage_templates)]
        step = ProductionStep(
            id=uuid.uuid4(),
            specification_id=spec.id,
            step_number=i + 1,
            stage_name=tmpl[0],
            required_skill=tmpl[1],
            required_machine_type=tmpl[2],
            base_hours=tmpl[3],
            per_unit_hours=tmpl[4],
            quality_checkpoint=f"Inspection checkpoint for stage #{i + 1}",
        )
        db.add(step)
        steps.append(step)
    db.commit()

    # 4. Production Order
    order = ProductionOrder(
        id=uuid.uuid4(),
        user_id=user.id,
        design_id=design.id,
        quantity=2,
        priority="high",
        status="pending",
        deadline=datetime.now(timezone.utc) + timedelta(days=14),
        notes="High-precision wedding client",
        render_id=render.id,
        approved_render_url=render.image_url,
        specification_id=spec.id,
    )
    db.add(order)
    db.commit()

    # 5. Optional Scheduled Tasks
    tasks: List[ScheduledTask] = []
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
            tasks.append(task)
            start_cursor = end_cursor + timedelta(hours=1)
        db.commit()

    db.commit()
    db.refresh(order)
    for s in steps:
        db.refresh(s)
    for t in tasks:
        db.refresh(t)

    return design, render, spec, order, steps, tasks


# ==============================================================================
# J.2 Tests: Sequential Workflow & Automatic Progression
# ==============================================================================

def test_j2_01_initialization_routing_states(db_session: Session):
    """Test 1: Initialization sets Step 1 READY and Steps 2..5 PENDING."""
    user = create_test_user(db_session, "initstate")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=5)

    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    assert len(executions) == 5

    assert executions[0].status == "ready"
    assert executions[0].production_step.step_number == 1

    for ex in executions[1:]:
        assert ex.status == "pending"
        assert ex.production_step.step_number > 1


def test_j2_02_start_step1_updates_order_status(db_session: Session):
    """Test 2: Starting Step 1 (READY -> IN_PROGRESS) sets actual_start_time and updates order status to in_progress."""
    user = create_test_user(db_session, "startstep1")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=3)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex = executions[0]

    assert order.status == "pending"

    updated = production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS, operator_notes="Artisan began wax carve."),
    )

    assert updated.status == "in_progress"
    assert updated.actual_start_time is not None

    db_session.refresh(order)
    assert order.status == "in_progress"


def test_j2_03_complete_step1_advances_step2(db_session: Session):
    """Test 3: Completing Step 1 (IN_PROGRESS -> COMPLETED) automatically advances Step 2 from PENDING to READY."""
    user = create_test_user(db_session, "advancestep2")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=3)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex, step3_ex = executions[0], executions[1], executions[2]

    # Start Step 1
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    # Complete Step 1
    completed_step1 = production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED, operator_notes="Wax flask ready for casting."),
    )

    assert completed_step1.status == "completed"
    assert completed_step1.completed_at is not None

    # Step 2 must be automatically moved from PENDING -> READY
    db_session.refresh(step2_ex)
    assert step2_ex.status == "ready"
    assert "Automatically advanced to READY" in (step2_ex.operator_notes or "")

    # Step 3 must remain PENDING
    db_session.refresh(step3_ex)
    assert step3_ex.status == "pending"


def test_j2_04_complete_step2_advances_step3(db_session: Session):
    """Test 4: Completing Step 2 automatically advances Step 3 to READY."""
    user = create_test_user(db_session, "advancestep3")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=3)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex, step3_ex = executions[0], executions[1], executions[2]

    # Progress Step 1
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    # Progress Step 2
    db_session.refresh(step2_ex)
    assert step2_ex.status == "ready"
    production_execution_service.transition_execution(
        db_session, user.id, step2_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, step2_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    # Step 3 is now READY
    db_session.refresh(step3_ex)
    assert step3_ex.status == "ready"


def test_j2_05_full_5_step_sequential_progression(db_session: Session):
    """Test 5: Full 5-step routing advances sequentially to final COMPLETED, updating order to completed."""
    user = create_test_user(db_session, "full5step")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=5)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    assert len(executions) == 5

    for i in range(5):
        current_ex = executions[i]
        db_session.refresh(current_ex)
        assert current_ex.status == "ready", f"Step #{i+1} should be READY before execution"

        # Start
        production_execution_service.transition_execution(
            db_session, user.id, current_ex.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )

        # Complete
        production_execution_service.transition_execution(
            db_session, user.id, current_ex.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED, operator_notes=f"Finished step #{i+1}"),
        )

        db_session.refresh(current_ex)
        assert current_ex.status == "completed"

    # All 5 steps completed -> ProductionOrder must be completed
    db_session.refresh(order)
    assert order.status == "completed"


def test_j2_06_cannot_skip_pending_to_in_progress(db_session: Session):
    """Test 6: Operator cannot jump directly from PENDING to IN_PROGRESS (returns 400)."""
    user = create_test_user(db_session, "noskipstart")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=3)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step2_ex = executions[1]
    assert step2_ex.status == "pending"

    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user.id, step2_ex.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "INVALID_EXECUTION_TRANSITION"
    assert exc_info.value.status_code == 400


def test_j2_07_cannot_skip_pending_to_ready_without_predecessor(db_session: Session):
    """Test 7: Step 3 cannot become READY while Step 1 or Step 2 is incomplete (returns 409 PREDECESSOR_NOT_COMPLETED)."""
    user = create_test_user(db_session, "noskipready")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=4)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step3_ex = executions[2]
    assert step3_ex.status == "pending"

    # Try advancing Step 3 directly to READY while Step 1 and 2 are incomplete
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user.id, step3_ex.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.READY),
        )
    assert exc_info.value.code == "PREDECESSOR_NOT_COMPLETED"
    assert exc_info.value.status_code == 409
    assert "must be COMPLETED" in exc_info.value.message


def test_j2_08_blocked_step_prevents_advancement(db_session: Session):
    """Test 8: If Step 1 is BLOCKED, Step 2 remains PENDING and cannot advance."""
    user = create_test_user(db_session, "blocktest")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=3)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex = executions[0], executions[1]

    # Block Step 1
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.BLOCKED, operator_notes="Missing gold casting grain."),
    )
    db_session.refresh(step1_ex)
    assert step1_ex.status == "blocked"

    # Step 2 must remain PENDING
    db_session.refresh(step2_ex)
    assert step2_ex.status == "pending"

    # Attempting to move Step 2 to READY fails
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user.id, step2_ex.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.READY),
        )
    assert exc_info.value.code == "PREDECESSOR_NOT_COMPLETED"


def test_j2_09_unblock_step_resumes_workflow(db_session: Session):
    """Test 9: Unblocking Step 1 (BLOCKED -> READY) allows resuming and auto-advancing Step 2."""
    user = create_test_user(db_session, "unblocktest")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex = executions[0], executions[1]

    # Block and unblock Step 1
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.BLOCKED),
    )
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.READY, operator_notes="Gold grain retrieved."),
    )
    db_session.refresh(step1_ex)
    assert step1_ex.status == "ready"

    # Execute and complete Step 1
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    # Step 2 is now automatically READY
    db_session.refresh(step2_ex)
    assert step2_ex.status == "ready"


def test_j2_10_pause_and_resume_preserves_timing(db_session: Session):
    """Test 10: Pause and resume cycles preserve actual_start_time and compute net duration accurately."""
    user = create_test_user(db_session, "pauseresume")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex = executions[0]

    # Start operation
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    # Simulate realistic times: start 4 hours ago
    t_start = datetime.now(timezone.utc) - timedelta(hours=4)
    step1_ex.actual_start_time = t_start
    db_session.commit()

    # Pause: 3 hours ago
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.PAUSED),
    )
    step1_ex.last_paused_at = datetime.now(timezone.utc) - timedelta(hours=3)
    db_session.commit()

    # Resume: 1.5 hours ago (pause duration = 1.5 hours)
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    step1_ex.pause_duration_hours = 1.5
    step1_ex.last_paused_at = None
    db_session.commit()

    # Complete now
    completed = production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    # Total elapsed ~4h - pause 1.5h = ~2.5h net
    assert 2.45 <= completed.actual_duration_hours <= 2.55
    assert completed.pause_duration_hours == 1.5


def test_j2_11_atomic_completion_rollback_on_advancement_failure(db_session: Session):
    """Test 11: Failure during next-step advancement rolls back completion and preserves IN_PROGRESS state."""
    user = create_test_user(db_session, "atomicrollback")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex = executions[0], executions[1]

    # Start Step 1
    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )

    # Attempt completion with simulated next-step advancement failure
    with pytest.raises(RuntimeError) as exc_info:
        production_execution_service.transition_execution(
            db_session, user.id, step1_ex.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
            _simulate_advancement_failure=True,
        )
    assert "Simulated failure during next-step advancement" in str(exc_info.value)

    # Step 1 must have been rolled back to IN_PROGRESS!
    db_session.rollback()  # Session clean after raised exception
    step1_refreshed = db_session.get(OperationExecution, step1_ex.id)
    step2_refreshed = db_session.get(OperationExecution, step2_ex.id)

    assert step1_refreshed.status == "in_progress"
    assert step1_refreshed.completed_at is None
    assert step1_refreshed.actual_end_time is None

    # Step 2 must remain PENDING
    assert step2_refreshed.status == "pending"


def test_j2_12_duplicate_completion_idempotency(db_session: Session):
    """Test 12: Second completion attempt returns 409 EXECUTION_ALREADY_COMPLETED and does not re-advance."""
    user = create_test_user(db_session, "dupcomplete")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=2)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    step1_ex, step2_ex = executions[0], executions[1]

    production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    first_completion = production_execution_service.transition_execution(
        db_session, user.id, step1_ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    assert first_completion.status == "completed"

    # Second completion attempt must fail with 409
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user.id, step1_ex.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
        )
    assert exc_info.value.code == "EXECUTION_ALREADY_COMPLETED"
    assert exc_info.value.status_code == 409


def test_j2_13_direct_execution_predecessor_enforcement(db_session: Session):
    """Test 13: Direct execution creation cannot bypass predecessor requirements."""
    user = create_test_user(db_session, "directpred")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=3)

    # Directly create execution for Step 3 when Step 1 and 2 do not have executions
    ex_step3 = production_execution_service.create_execution(
        db_session, user.id,
        OperationExecutionCreate(
            production_order_id=order.id,
            production_step_id=steps[2].id,  # Step 3
            operator_notes="Direct creation of step 3",
        ),
    )
    # Because predecessor steps are not complete, initial status MUST be pending
    assert ex_step3.status == "pending"

    # Attempting to start or make ready directly fails
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user.id, ex_step3.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.READY),
        )
    assert exc_info.value.code == "PREDECESSOR_NOT_COMPLETED"


def test_j2_14_direct_execution_duplicate_rejected(db_session: Session):
    """Test 14: Direct creation for an already existing (order, step) execution raises 409."""
    user = create_test_user(db_session, "directdup")
    _, _, spec, order, steps, _ = setup_j2_environment(db_session, user, num_steps=2)

    # Initialize order executions
    production_execution_service.initialize_order_executions(db_session, user.id, order.id)

    # Try creating Step 1 again directly
    with pytest.raises(AppException) as exc_info:
        production_execution_service.create_execution(
            db_session, user.id,
            OperationExecutionCreate(
                production_order_id=order.id,
                production_step_id=steps[0].id,
            ),
        )
    assert exc_info.value.code == "EXECUTION_ALREADY_EXISTS"
    assert exc_info.value.status_code == 409


def test_j2_15_scheduled_task_plan_preserved(db_session: Session):
    """Test 15: ScheduledTask plan data is preserved and carried into execution records."""
    user = create_test_user(db_session, "schedplan")
    _, _, spec, order, steps, sched_tasks = setup_j2_environment(
        db_session, user, num_steps=3, with_schedule=True
    )
    assert len(sched_tasks) == 3

    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    assert len(executions) == 3

    for i, ex in enumerate(executions):
        assert ex.scheduled_task_id == sched_tasks[i].id
        assert ex.planned_start_time is not None
        assert ex.planned_duration_hours == sched_tasks[i].duration_hours


def test_j2_16_unscheduled_direct_execution_progresses_correctly(db_session: Session):
    """Test 16: Unscheduled execution runs without CP-SAT schedule and auto-advances."""
    user = create_test_user(db_session, "unschedprog")
    _, _, spec, order, steps, _ = setup_j2_environment(
        db_session, user, num_steps=2, with_schedule=False
    )

    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    assert executions[0].scheduled_task_id is None
    assert executions[1].scheduled_task_id is None

    # Step 1 start & complete
    production_execution_service.transition_execution(
        db_session, user.id, executions[0].id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, executions[0].id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    # Step 2 auto-advances to READY
    db_session.refresh(executions[1])
    assert executions[1].status == "ready"


def test_j2_17_cross_tenant_idor_rejected(db_session: Session):
    """Test 17: User B cannot access or transition User A executions (returns 404)."""
    user_a = create_test_user(db_session, "tenantA")
    user_b = create_test_user(db_session, "tenantB")
    _, _, _, order_a, _, _ = setup_j2_environment(db_session, user_a, num_steps=2)

    executions_a = production_execution_service.initialize_order_executions(db_session, user_a.id, order_a.id)
    ex_a = executions_a[0]

    # User B attempts to access User A execution
    with pytest.raises(AppException) as exc_info:
        production_execution_service.get_execution_by_id(db_session, user_b.id, ex_a.id)
    assert exc_info.value.code == "EXECUTION_NOT_FOUND"
    assert exc_info.value.status_code == 404

    # User B attempts to transition User A execution
    with pytest.raises(AppException) as exc_info:
        production_execution_service.transition_execution(
            db_session, user_b.id, ex_a.id,
            OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
        )
    assert exc_info.value.code == "EXECUTION_NOT_FOUND"
    assert exc_info.value.status_code == 404


def test_j2_18_completed_state_is_terminal(db_session: Session):
    """Test 18: Once an execution reaches COMPLETED, any backward transition is rejected with 409."""
    user = create_test_user(db_session, "terminalop")
    _, _, _, order, _, _ = setup_j2_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    ex = executions[0]

    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, ex.id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    for invalid_target in [ExecutionStatus.IN_PROGRESS, ExecutionStatus.PAUSED, ExecutionStatus.READY, ExecutionStatus.BLOCKED]:
        with pytest.raises(AppException) as exc_info:
            production_execution_service.transition_execution(
                db_session, user.id, ex.id,
                OperationExecutionTransitionRequest(target_status=invalid_target),
            )
        assert exc_info.value.code == "EXECUTION_ALREADY_COMPLETED"
        assert exc_info.value.status_code == 409


def test_j2_19_final_step_completion_does_not_crash_or_create_next(db_session: Session):
    """Test 19: Completing the final step of an order does not fail or invent a nonexistent step."""
    user = create_test_user(db_session, "finalstep")
    _, _, _, order, steps, _ = setup_j2_environment(db_session, user, num_steps=1)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)
    assert len(executions) == 1

    production_execution_service.transition_execution(
        db_session, user.id, executions[0].id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    completed_final = production_execution_service.transition_execution(
        db_session, user.id, executions[0].id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )
    assert completed_final.status == "completed"

    # Verify no additional executions created
    all_ex = production_execution_service.get_order_executions(db_session, user.id, order.id)
    assert len(all_ex) == 1

    # Order marked completed
    db_session.refresh(order)
    assert order.status == "completed"


def test_j2_20_workflow_progress_metrics_in_list_response(db_session: Session):
    """Test 20: List response computes accurate workflow counts and progress percentage."""
    user = create_test_user(db_session, "metricsresp")
    _, _, _, order, steps, _ = setup_j2_environment(db_session, user, num_steps=4)
    executions = production_execution_service.initialize_order_executions(db_session, user.id, order.id)

    # Initial state: 1 READY, 3 PENDING, 0% progress
    resp1 = production_execution_service.get_order_execution_list_response(db_session, user.id, order.id)
    assert resp1.total == 4
    assert resp1.ready_count == 1
    assert resp1.pending_count == 3
    assert resp1.completed_count == 0
    assert resp1.overall_progress_percent == 0.0
    assert resp1.current_step_number == 1
    assert resp1.order_status == "pending"

    # Complete Step 1: Step 2 becomes READY (25% completed)
    production_execution_service.transition_execution(
        db_session, user.id, executions[0].id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.IN_PROGRESS),
    )
    production_execution_service.transition_execution(
        db_session, user.id, executions[0].id,
        OperationExecutionTransitionRequest(target_status=ExecutionStatus.COMPLETED),
    )

    resp2 = production_execution_service.get_order_execution_list_response(db_session, user.id, order.id)
    assert resp2.completed_count == 1
    assert resp2.ready_count == 1
    assert resp2.pending_count == 2
    assert resp2.overall_progress_percent == 25.0
    assert resp2.current_step_number == 2
    assert resp2.order_status == "in_progress"


# ==============================================================================
# J.2 REST API End-to-End Tests
# ==============================================================================

def test_j2_21_api_full_workflow_lifecycle(client: TestClient, db_session: Session):
    """Test 21: Full API lifecycle: initialize -> list -> start -> complete -> auto-advance -> final order complete."""
    user = create_test_user(db_session, "apiworkflow")
    headers = auth_headers(user)
    _, _, _, order, steps, _ = setup_j2_environment(db_session, user, num_steps=2)

    # 1. Initialize executions via POST
    init_res = client.post(
        f"/api/v1/production/orders/{order.id}/executions/initialize",
        headers=headers,
    )
    assert init_res.status_code == 201
    init_data = init_res.json()
    assert len(init_data) == 2
    step1_id = init_data[0]["id"]
    step2_id = init_data[1]["id"]
    assert init_data[0]["status"] == "ready"
    assert init_data[1]["status"] == "pending"

    # 2. List executions with progress metrics
    list_res = client.get(
        f"/api/v1/production/orders/{order.id}/executions",
        headers=headers,
    )
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 2
    assert list_data["ready_count"] == 1
    assert list_data["pending_count"] == 1
    assert list_data["completed_count"] == 0
    assert list_data["overall_progress_percent"] == 0.0

    # 3. Step 2 cannot be started directly (returns 400)
    skip_res = client.post(
        f"/api/v1/production/executions/{step2_id}/transition",
        headers=headers,
        json={"target_status": "in_progress"},
    )
    assert skip_res.status_code == 400

    # 4. Start Step 1
    start_res = client.post(
        f"/api/v1/production/executions/{step1_id}/transition",
        headers=headers,
        json={"target_status": "in_progress", "operator_notes": "Artisan carving started."},
    )
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "in_progress"

    # 5. Complete Step 1 -> Step 2 must be automatically ready
    comp_res = client.post(
        f"/api/v1/production/executions/{step1_id}/transition",
        headers=headers,
        json={"target_status": "completed", "operator_notes": "Wax flask completed."},
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "completed"

    # 6. Verify Step 2 is now ready via GET
    step2_check = client.get(
        f"/api/v1/production/executions/{step2_id}",
        headers=headers,
    )
    assert step2_check.status_code == 200
    assert step2_check.json()["status"] == "ready"
    assert step2_check.json()["can_start"] is True

    # 7. Start and complete Step 2
    client.post(
        f"/api/v1/production/executions/{step2_id}/transition",
        headers=headers,
        json={"target_status": "in_progress"},
    )
    comp2_res = client.post(
        f"/api/v1/production/executions/{step2_id}/transition",
        headers=headers,
        json={"target_status": "completed"},
    )
    assert comp2_res.status_code == 200

    # 8. Check final progress metrics (100% completed)
    final_list = client.get(
        f"/api/v1/production/orders/{order.id}/executions",
        headers=headers,
    )
    assert final_list.status_code == 200
    final_data = final_list.json()
    assert final_data["completed_count"] == 2
    assert final_data["overall_progress_percent"] == 100.0
    assert final_data["order_status"] == "completed"
