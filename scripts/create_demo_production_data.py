"""
JewelMind — Idempotent Demo Production Dataset Seeder

Creates a realistic, complete, internally-consistent demo production dataset
for the authenticated demo user (usernamechef2343@gmail.com).

Workflow exercised:
1. User lookup
2. Design creation / reuse: 'JewelMind Demo Emerald Pendant'
3. Approved Render creation / reuse: bound to design
4. Production Specification: BOM (18K Yellow Gold, Oval Emerald), 6 sequential routing steps, status='approved'
5. Workshop Artisans: Rahul, Priya, Aman with validated craft skills
6. Workshop Machinery: Casting Station, Setting Station, Polishing Station
7. CP-SAT Scheduling: generates conflict-free ScheduledTasks
8. Shop-Floor Execution Initialization: sequential OperationExecutions linked to tasks
9. Realistic Execution Progress:
   - Step 1 (CAD & 3D Wax Pattern): COMPLETED, with Material Consumption & QC PASS
   - Step 2 (Investment Casting): IN_PROGRESS with Rahul & Casting Station actively assigned
   - Steps 3-6: PENDING in sequence
10. Idempotent: checks for existing demo records before inserting.
"""

import sys
import os
import uuid
import datetime
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.models.design import Design, DesignRender
from app.models.specification import (
    ProductionSpecification,
    ProductionMaterial,
    ProductionGemstone,
    ProductionStep,
)
from app.models.production import ProductionOrder, Worker, Machine
from app.models.schedule import ProductionSchedule, ScheduledTask
from app.models.execution import (
    OperationExecution,
    MaterialConsumption,
    QualityCheck,
)
from app.services.production_optimization_service import production_optimization_service
from app.services.production_execution_service import production_execution_service
from app.schemas.optimization import OptimizationRequest
from app.schemas.execution import (
    ExecutionStatus,
    QualityCheckResult,
    DefectSeverity,
    OperationExecutionTransitionRequest,
    MaterialConsumptionCreate,
    QualityCheckCreate,
)


TARGET_USER_EMAIL = "usernamechef2343@gmail.com"
DEMO_TAG = "JM-DEMO-001"


def advance_demo_executions(db: Session, user_id: uuid.UUID, order: ProductionOrder, executions: list, workers: list, machines: list):
    """Advances Step 1 to COMPLETED with material & QC PASS, and Step 2 to IN_PROGRESS with Rahul & Casting Station."""
    exec_1 = executions[0]  # CAD & 3D Wax Pattern
    exec_2 = executions[1]  # Investment Casting & Spruing

    if exec_1.status != ExecutionStatus.COMPLETED.value:
        if exec_1.status == ExecutionStatus.READY.value:
            # Transition Step 1: READY -> IN_PROGRESS
            production_execution_service.transition_execution(
                db=db,
                user_id=user_id,
                execution_id=exec_1.id,
                req=OperationExecutionTransitionRequest(
                    target_status=ExecutionStatus.IN_PROGRESS,
                    operator_notes="DEMO DATA — CAD pattern and casting sprue modeled in MatrixGold",
                ),
            )

        # Record Material Consumption on Step 1 if not already recorded
        existing_mat = list(db.scalars(
            select(MaterialConsumption).where(MaterialConsumption.operation_execution_id == exec_1.id)
        ).all())
        if not existing_mat:
            mat_in = MaterialConsumptionCreate(
                material_name="18K Yellow Gold",
                material_type="METAL",
                unit="g",
                planned_quantity=8.50,
                actual_quantity=8.70,
                wastage_quantity=0.20,
                wastage_reason="Standard sprue cutoff and crucible loss",
                notes="DEMO DATA — Initial casting alloy melt",
            )
            production_execution_service.record_material_consumption(
                db=db,
                user_id=user_id,
                execution_id=exec_1.id,
                payload=mat_in,
            )

        # Transition Step 1: IN_PROGRESS -> COMPLETED
        production_execution_service.transition_execution(
            db=db,
            user_id=user_id,
            execution_id=exec_1.id,
            req=OperationExecutionTransitionRequest(
                target_status=ExecutionStatus.COMPLETED,
                operator_notes="DEMO DATA — Wax pattern precision verified against 3D CAD mesh",
            ),
        )

        # Record QC PASS on Step 1 if not already recorded
        existing_qc = list(db.scalars(
            select(QualityCheck).where(QualityCheck.operation_execution_id == exec_1.id)
        ).all())
        if not existing_qc:
            qc_in = QualityCheckCreate(
                result=QualityCheckResult.PASS,
                defect_severity=DefectSeverity.NONE,
                notes="DEMO DATA — Wax pattern precision verified against 3D CAD mesh",
                checked_by="QC Inspector Rahul V.",
            )
            production_execution_service.record_quality_check(
                db=db,
                user_id=user_id,
                execution_id=exec_1.id,
                payload=qc_in,
            )

    # Step 2 is now automatically READY!
    db.refresh(exec_2)

    if exec_2.status != ExecutionStatus.IN_PROGRESS.value:
        rahul = next((w for w in workers if "Rahul" in w.name), workers[0])
        casting_station = next((m for m in machines if "Casting" in m.name), machines[0])

        production_execution_service.assign_worker(
            db=db,
            user_id=user_id,
            execution_id=exec_2.id,
            worker_id=rahul.id,
        )
        production_execution_service.assign_machine(
            db=db,
            user_id=user_id,
            execution_id=exec_2.id,
            machine_id=casting_station.id,
        )

        # Transition Step 2: READY -> IN_PROGRESS
        production_execution_service.transition_execution(
            db=db,
            user_id=user_id,
            execution_id=exec_2.id,
            req=OperationExecutionTransitionRequest(
                target_status=ExecutionStatus.IN_PROGRESS,
                operator_notes="DEMO DATA — Flask preheated to 650°C and loaded in vacuum casting chamber",
            ),
        )

    db.commit()
    print(f"[8/8] Successfully established live production state:")
    print(f"       - Order status: IN_PROGRESS")
    print(f"       - Operation 1 (CAD): COMPLETED (Material recorded + QC PASS)")
    print(f"       - Operation 2 (Casting): IN_PROGRESS (Artisan Rahul & Casting Station actively running)")
    print(f"       - Operations 3-6: PENDING sequential pipeline")
    print("\n[SUCCESS] DEMO PRODUCTION DATASET FULLY SEEDED AND READY!")


def seed_demo_dataset():
    db: Session = SessionLocal()
    try:
        # 1. User Lookup
        user = db.scalar(select(User).where(User.email == TARGET_USER_EMAIL))
        if not user:
            print(f"[ERROR] Target user '{TARGET_USER_EMAIL}' not found in database.")
            return

        user_id = user.id
        print(f"[1/8] Located demo user: {user.email} (ID: {user_id})")

        # Check for existing DEMO order (Idempotency)
        existing_order = db.scalar(
            select(ProductionOrder).where(
                ProductionOrder.user_id == user_id,
                ProductionOrder.notes.contains(DEMO_TAG),
            )
        )
        if existing_order:
            print(f"[INFO] Demo order '{DEMO_TAG}' already exists (ID: {existing_order.id}).")
            executions = list(db.scalars(
                select(OperationExecution)
                .where(OperationExecution.production_order_id == existing_order.id)
                .order_by(OperationExecution.created_at.asc())
            ).all())
            print(f"       Found {len(executions)} operations.")
            if len(executions) >= 2 and executions[0].status == ExecutionStatus.COMPLETED.value and executions[1].status == ExecutionStatus.IN_PROGRESS.value:
                print("       Dataset already in target state (Step 1 COMPLETED, Step 2 IN_PROGRESS).")
                for ex in executions:
                    step_name = ex.production_step.stage_name if ex.production_step else "Unknown"
                    print(f"       - Step {ex.production_step.step_number if ex.production_step else '?'}: {step_name} [{ex.status.upper()}]")
                return

            print("       Advancing existing demo order operations to target state...")
            created_workers = list(db.scalars(select(Worker).where(Worker.user_id == user_id)).all())
            created_machines = list(db.scalars(select(Machine).where(Machine.user_id == user_id)).all())
            advance_demo_executions(db, user_id, existing_order, executions, created_workers, created_machines)
            return

        # 2. Design Creation / Reuse
        design = db.scalar(
            select(Design).where(
                Design.user_id == user_id,
                Design.name == "JewelMind Demo Emerald Pendant",
            )
        )
        if not design:
            design = Design(
                user_id=user_id,
                name="JewelMind Demo Emerald Pendant",
                category="Pendant",
                description="Luxury handcrafted 18k yellow gold pendant with bezel-set vivid green oval emerald.",
                status="rendered",
            )
            db.add(design)
            db.flush()
            print(f"[2/8] Created Demo Design: '{design.name}' (ID: {design.id})")
        else:
            print(f"[2/8] Reusing existing Demo Design: (ID: {design.id})")

        # 3. Approved Design Render
        render = db.scalar(
            select(DesignRender).where(
                DesignRender.design_id == design.id,
                DesignRender.is_approved_for_production == True,
            )
        )
        if not render:
            render = DesignRender(
                design_id=design.id,
                user_id=user_id,
                version_number=1,
                render_mode="studio",
                prompt="18k yellow gold emerald oval stone pendant, museum grade macro jewelry photography",
                enhanced_prompt="Masterpiece 18k yellow gold pendant with high-clarity bezel-set oval emerald, polished finish, studio lighting",
                image_url="/api/v1/ai/render/outputs/demo_emerald_pendant.png",
                is_approved_for_production=True,
                control_type="none",
                control_strength=0.0,
                seed=424242,
            )
            db.add(render)
            db.flush()
            print(f"[3/8] Created and Approved Demo Render: (ID: {render.id})")
        else:
            print(f"[3/8] Reusing approved Demo Render: (ID: {render.id})")

        # 4. Production Specification
        spec = db.scalar(
            select(ProductionSpecification).where(
                ProductionSpecification.user_id == user_id,
                ProductionSpecification.design_id == design.id,
                ProductionSpecification.render_id == render.id,
                ProductionSpecification.status == "approved",
            )
        )
        if not spec:
            spec = ProductionSpecification(
                user_id=user_id,
                design_id=design.id,
                render_id=render.id,
                version_number=1,
                status="approved",
                category="Pendant",
                estimated_rough_metal_weight_grams=8.50,
                estimated_finished_metal_weight_grams=7.80,
                total_gemstone_count=1,
                estimated_total_bench_hours=12.0,
                complexity_rating="moderate",
                fabrication_notes="Master Artisan Review: Verify bezel wall thickness (min 0.8mm) for secure emerald seat.",
            )
            db.add(spec)
            db.flush()

            # Add BOM Materials
            material = ProductionMaterial(
                specification_id=spec.id,
                metal_type="Gold",
                metal_purity="18K",
                metal_color="Yellow",
                metal_finish="High Polish",
                estimated_weight_grams=8.50,
                casting_loss_percentage=8.2,
            )
            db.add(material)

            # Add Gemstone
            gemstone = ProductionGemstone(
                specification_id=spec.id,
                gemstone_type="Emerald",
                cut_shape="Oval",
                stone_count=1,
                estimated_carat_weight=1.50,
                approximate_dimensions_mm="8.0 x 6.0 mm",
                setting_type="Bezel",
                is_center_stone=True,
            )
            db.add(gemstone)

            # Add Routing Steps
            steps_data = [
                (1, "CAD & 3D Wax Pattern", "cad", None, 2.0, 0.0, "High precision 3D wax printing of pendant setting"),
                (2, "Investment Casting & Spruing", "casting", "casting", 3.0, 0.0, "Vacuum casting in 18k yellow gold alloy"),
                (3, "De-spruing & Metal Preparation", "metal_preparation", None, 1.5, 0.0, "Cut sprues, ultrasonic clean, and file seams"),
                (4, "Stone Setting & Assembly", "stone_setting", "stone_setting", 2.5, 0.0, "Hand bezel-setting of center oval emerald"),
                (5, "Polishing & Finishing", "polishing", "polishing", 2.0, 0.0, "Multi-stage rogue buffing to mirror finish"),
                (6, "Final Quality Inspection", "quality_inspection", None, 1.0, 0.0, "Microscopic prong, bezel, and surface audit"),
            ]
            for step_num, name, skill, mach_type, base_h, per_unit_h, desc in steps_data:
                p_step = ProductionStep(
                    specification_id=spec.id,
                    step_number=step_num,
                    stage_name=name,
                    required_skill=skill,
                    required_machine_type=mach_type,
                    base_hours=base_h,
                    per_unit_hours=per_unit_h,
                    description=desc,
                    quality_checkpoint=f"Inspect {name} specifications against blueprint",
                )
                db.add(p_step)

            db.flush()
            print(f"[4/8] Created Approved Production Specification with BOM & 6 Steps: (ID: {spec.id})")
        else:
            print(f"[4/8] Reusing existing Production Specification: (ID: {spec.id})")

        # 5. Workshop Artisans (Workers)
        workers_info = [
            ("Demo Artisan — Rahul", "general", 8.0),
            ("Demo Artisan — Priya", "general", 8.0),
            ("Demo Artisan — Aman", "general", 8.0),
        ]
        created_workers = []
        for name, skills, cap in workers_info:
            w = db.scalar(select(Worker).where(Worker.user_id == user_id, Worker.name == name))
            if not w:
                w = Worker(
                    user_id=user_id,
                    name=name,
                    skill=skills,
                    capacity_hours_per_day=cap,
                    is_available=True,
                )
                db.add(w)
                db.flush()
            else:
                w.skill = skills
                w.is_available = True
                db.flush()
            created_workers.append(w)
        print(f"[5/8] Verified {len(created_workers)} Workshop Artisans (Rahul, Priya, Aman)")

        # 6. Workshop Machinery
        machines_info = [
            ("Demo Casting Station", "casting", 8.0),
            ("Demo Setting Bench", "stone_setting", 8.0),
            ("Demo Polishing Lathe", "polishing", 8.0),
        ]
        created_machines = []
        for name, m_type, cap in machines_info:
            m = db.scalar(select(Machine).where(Machine.user_id == user_id, Machine.name == name))
            if not m:
                m = Machine(
                    user_id=user_id,
                    name=name,
                    machine_type=m_type,
                    capacity_hours_per_day=cap,
                    is_available=True,
                )
                db.add(m)
                db.flush()
            else:
                m.machine_type = m_type
                m.is_available = True
                db.flush()
            created_machines.append(m)
        print(f"[6/8] Verified {len(created_machines)} Workshop Machines (Casting, Setting, Polishing)")

        # 7. Create Production Order
        deadline = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
        order = ProductionOrder(
            user_id=user_id,
            design_id=design.id,
            specification_id=spec.id,
            render_id=render.id,
            approved_render_url=render.image_url,
            quantity=5,
            priority="medium",
            status="in_progress",
            deadline=deadline,
            notes=f"[{DEMO_TAG}] JewelMind Showcase — Handcrafted Emerald Pendant Batch",
        )
        db.add(order)
        db.flush()
        print(f"[7/8] Created Production Order: '{order.notes}' (ID: {order.id})")

        # 8. Optimize & Schedule via CP-SAT
        opt_req = OptimizationRequest(
            start_date=datetime.datetime.now(datetime.timezone.utc),
            horizon_days=14,
            order_ids=[order.id],
        )
        schedule_resp = production_optimization_service.optimize(
            db=db,
            user_id=user_id,
            request=opt_req,
        )
        makespan = schedule_resp.metrics.makespan_hours if schedule_resp.metrics else 0.0
        print(f"       CP-SAT Solver generated schedule: makespan={makespan}h status={schedule_resp.solver_status}")

        # 9. Initialize Executions
        executions = production_execution_service.initialize_order_executions(
            db=db,
            user_id=user_id,
            order_id=order.id,
        )
        print(f"       Initialized {len(executions)} sequential shop-floor operations")

        # 10. Simulate Realistic Progress (Step 1 Completed, Step 2 In-Progress)
        advance_demo_executions(db, user_id, order, executions, created_workers, created_machines)

    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Seeding failed: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_dataset()
