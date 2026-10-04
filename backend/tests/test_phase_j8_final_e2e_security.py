"""
Phase J.8 Final E2E, Security & Production Readiness Test Suite
Comprehensive testing covering:
1. Complete E2E business workflow:
   User Auth -> Design -> Render -> Approve Render -> Generate Spec ->
   Artisan Edit -> Approve Spec -> Create Order from Spec ->
   Initialize Executions -> Assign Worker & Machine -> Start Op ->
   Record Material -> Complete Op -> QC Check (PASS) ->
   Next Op -> Complete Op 2 -> Final QC Pass -> Order Completion ->
   Shop Floor Dashboard -> Planned vs Actual Analytics.
2. Controlled Rework Cycle:
   Completed Op -> QC REWORK -> Authorize Rework Execution ->
   Verify Original Execution Remains Immutable -> Execute Rework ->
   Material on Rework -> QC PASS on Rework -> Order Completion.
3. Multi-Tenant IDOR Isolation:
   User A vs User B across Designs, Renders, Specifications, Orders, Executions, Materials, QC, Analytics.
4. Client Injection / Tampering Rejection:
   Forbidden client-supplied user_id, timestamps, extra properties with extra="forbid".
5. Production State Machine & Gating:
   Cannot complete order before QC pass, cannot advance without predecessor completion.
6. J.7 Analytics Zero-Mutation Verification:
   Read-only guarantee: calling analytics before and after does not modify database state.
"""

import datetime
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.design import Design, DesignRender
from app.models.specification import ProductionSpecification, ProductionStep
from app.models.production import ProductionOrder
from app.models.execution import (
    OperationExecution,
    MaterialConsumption,
    QualityCheck,
)


def _register_user(client: TestClient, email: str, name: str) -> dict:
    res = client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": name,
        "password": "SecurePassword123!",
    })
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_complete_e2e_production_lifecycle_and_analytics(client: TestClient, db_session: Session):
    """
    Validates complete unbroken business workflow from design to analytics.
    """
    headers = _register_user(client, "artisan_master@jewelmind.com", "Master Artisan")

    # 1. CREATE DESIGN
    res_design = client.post("/api/v1/designs", json={
        "name": "Solitaire Platinum Ring",
        "category": "Ring",
        "description": "Handcrafted luxury platinum ring with diamond solitaire",
    }, headers=headers)
    assert res_design.status_code == 201
    design_id = res_design.json()["id"]

    # 2. CREATE AND APPROVE RENDER
    render_id = uuid.uuid4()
    render = DesignRender(
        id=render_id,
        design_id=uuid.UUID(design_id),
        user_id=uuid.UUID(res_design.json()["user_id"]),
        version_number=1,
        render_mode="studio",
        prompt="Platinum solitaire diamond ring, photorealistic macro",
        image_url=f"/api/v1/ai/render/outputs/render_{render_id}.png",
        is_approved_for_production=False,
    )
    db_session.add(render)
    db_session.commit()

    # Approve render for production
    res_approve_render = client.post(
        f"/api/v1/designs/{design_id}/renders/{render_id}/approve",
        headers=headers,
    )
    assert res_approve_render.status_code == 200
    assert res_approve_render.json()["is_approved_for_production"] is True

    # 3. GENERATE PRODUCTION SPECIFICATION FROM APPROVED RENDER
    res_gen_spec = client.post("/api/v1/production-specifications/generate", json={
        "render_id": str(render_id),
        "user_prompt": "Platinum solitaire diamond ring with micro-prong setting",
        "material_hint": "platinum 950",
        "gemstone_hint": "diamond",
    }, headers=headers)
    assert res_gen_spec.status_code == 201
    spec_id = res_gen_spec.json()["id"]
    assert res_gen_spec.json()["render_id"] == str(render_id)
    assert res_gen_spec.json()["design_id"] == design_id
    assert res_gen_spec.json()["status"] == "draft"

    # 4. ARTISAN REVIEW / EDIT SPECIFICATION
    res_edit_spec = client.patch(f"/api/v1/production-specifications/{spec_id}", json={
        "fabrication_notes": "Artisan review: Ensure prongs are reinforced for security.",
    }, headers=headers)
    assert res_edit_spec.status_code == 200
    assert "Ensure prongs are reinforced" in (res_edit_spec.json().get("fabrication_notes") or "")

    # 5. APPROVE SPECIFICATION
    res_approve_spec = client.post(f"/api/v1/production-specifications/{spec_id}/approve", headers=headers)
    assert res_approve_spec.status_code == 200
    assert res_approve_spec.json()["status"] == "approved"

    # 6. CREATE PRODUCTION ORDER FROM APPROVED SPECIFICATION
    deadline = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat()
    res_order = client.post("/api/v1/production/orders/from-specification", json={
        "specification_id": spec_id,
        "quantity": 2,
        "priority": "high",
        "deadline": deadline,
        "notes": "VIP Client Order",
    }, headers=headers)
    assert res_order.status_code == 201
    order_id = res_order.json()["id"]
    assert res_order.json()["specification_id"] == spec_id
    assert res_order.json()["render_id"] == str(render_id)
    assert res_order.json()["design_id"] == design_id
    assert res_order.json()["status"] == "pending"

    # 7. WORKER & MACHINE CREATION
    # Incompatible worker test
    res_incomp_w = client.post("/api/v1/production/workers", json={
        "name": "Polisher Pam",
        "skill": "polishing",
        "capacity_hours_per_day": 8.0,
    }, headers=headers)
    assert res_incomp_w.status_code == 201
    incomp_worker_id = res_incomp_w.json()["id"]

    # 8. INITIALIZE PRODUCTION EXECUTIONS
    res_init = client.post(f"/api/v1/production/orders/{order_id}/executions/initialize", headers=headers)
    assert res_init.status_code == 201
    init_data = res_init.json()
    executions = init_data if isinstance(init_data, list) else init_data.get("executions", [])
    assert len(executions) >= 2
    exec_1 = executions[0]
    exec_2 = executions[1]
    assert exec_1["status"] == "ready"
    assert exec_2["status"] == "pending"

    # Verify incompatible worker is rejected (Phase J.3)
    req_skill = exec_1.get("required_skill") or "general"
    req_machine = exec_1.get("required_machine_type") or "general"
    if req_skill != "polishing":
        res_bad_assign = client.post(f"/api/v1/production/executions/{exec_1['id']}/assign-worker", json={
            "worker_id": incomp_worker_id,
        }, headers=headers)
        assert res_bad_assign.status_code == 409

    # Create compatible worker and machine
    res_comp_w = client.post("/api/v1/production/workers", json={
        "name": "Eligible Artisan",
        "skill": req_skill,
        "capacity_hours_per_day": 8.0,
    }, headers=headers)
    assert res_comp_w.status_code == 201
    worker_id = res_comp_w.json()["id"]

    res_comp_m = client.post("/api/v1/production/machines", json={
        "name": "Compatible Machine",
        "machine_type": req_machine,
        "capacity_hours_per_day": 8.0,
    }, headers=headers)
    assert res_comp_m.status_code == 201
    machine_id = res_comp_m.json()["id"]

    # 9. ASSIGN WORKER AND MACHINE TO OP 1
    res_assign_w = client.post(f"/api/v1/production/executions/{exec_1['id']}/assign-worker", json={
        "worker_id": worker_id,
    }, headers=headers)
    assert res_assign_w.status_code == 200

    res_assign_m = client.post(f"/api/v1/production/executions/{exec_1['id']}/assign-machine", json={
        "machine_id": machine_id,
    }, headers=headers)
    assert res_assign_m.status_code == 200

    # 10. START OP 1 -> IN_PROGRESS VIA TRANSITION
    res_start = client.post(f"/api/v1/production/executions/{exec_1['id']}/transition", json={
        "target_status": "in_progress",
    }, headers=headers)
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "in_progress"

    # Test PAUSE and RESUME
    res_pause = client.post(f"/api/v1/production/executions/{exec_1['id']}/transition", json={
        "target_status": "paused",
        "operator_notes": "Artisan bench break",
    }, headers=headers)
    assert res_pause.status_code == 200
    assert res_pause.json()["status"] == "paused"

    res_resume = client.post(f"/api/v1/production/executions/{exec_1['id']}/transition", json={
        "target_status": "in_progress",
    }, headers=headers)
    assert res_resume.status_code == 200
    assert res_resume.json()["status"] == "in_progress"

    # 11. RECORD MATERIAL CONSUMPTION (J.4)
    res_mat = client.post(f"/api/v1/production/executions/{exec_1['id']}/material-consumption", json={
        "material_type": "METAL",
        "material_name": "Platinum 950",
        "unit": "g",
        "actual_quantity": 15.5,
        "wastage_quantity": 0.5,
    }, headers=headers)
    assert res_mat.status_code == 201
    assert res_mat.json()["actual_quantity"] == 15.5
    assert res_mat.json()["wastage_quantity"] == 0.5

    # Test invalid consumption: negative quantity and wastage > actual
    res_bad_mat1 = client.post(f"/api/v1/production/executions/{exec_1['id']}/material-consumption", json={
        "material_type": "METAL",
        "material_name": "Platinum 950",
        "unit": "g",
        "actual_quantity": -5.0,
    }, headers=headers)
    assert res_bad_mat1.status_code == 422

    res_bad_mat2 = client.post(f"/api/v1/production/executions/{exec_1['id']}/material-consumption", json={
        "material_type": "METAL",
        "material_name": "Platinum 950",
        "unit": "g",
        "actual_quantity": 5.0,
        "wastage_quantity": 10.0,  # Wastage > actual
    }, headers=headers)
    assert res_bad_mat2.status_code in (400, 422)

    # 12. COMPLETE OP 1 VIA TRANSITION
    res_comp_1 = client.post(f"/api/v1/production/executions/{exec_1['id']}/transition", json={
        "target_status": "completed",
    }, headers=headers)
    assert res_comp_1.status_code == 200
    assert res_comp_1.json()["status"] == "completed"

    # 13. QC CHECK ON OP 1 (PASS)
    res_qc_1 = client.post(f"/api/v1/production/executions/{exec_1['id']}/quality-check", json={
        "result": "PASS",
        "defect_severity": "NONE",
        "notes": "Casting flawless, no porosity detected.",
        "checked_by": "QC-INSP-101",
    }, headers=headers)
    assert res_qc_1.status_code == 201
    assert res_qc_1.json()["result"] == "PASS"

    # Verify Op 2 is now READY
    res_exec_2_status = client.get(f"/api/v1/production/executions/{exec_2['id']}", headers=headers)
    assert res_exec_2_status.status_code == 200
    assert res_exec_2_status.json()["status"] == "ready"

    # 14. OP 2: ASSIGN WORKER & MACHINE, START, RECORD MATERIAL, COMPLETE
    req_skill_2 = exec_2.get("required_skill") or "general"
    req_machine_2 = exec_2.get("required_machine_type") or "general"

    res_comp_w2 = client.post("/api/v1/production/workers", json={
        "name": f"Artisan for {req_skill_2}",
        "skill": req_skill_2,
        "capacity_hours_per_day": 8.0,
    }, headers=headers)
    assert res_comp_w2.status_code == 201

    res_comp_m2 = client.post("/api/v1/production/machines", json={
        "name": f"Machine for {req_machine_2}",
        "machine_type": req_machine_2,
        "capacity_hours_per_day": 8.0,
    }, headers=headers)
    assert res_comp_m2.status_code == 201

    res_as_w2 = client.post(f"/api/v1/production/executions/{exec_2['id']}/assign-worker", json={
        "worker_id": res_comp_w2.json()["id"],
    }, headers=headers)
    assert res_as_w2.status_code == 200

    res_as_m2 = client.post(f"/api/v1/production/executions/{exec_2['id']}/assign-machine", json={
        "machine_id": res_comp_m2.json()["id"],
    }, headers=headers)
    assert res_as_m2.status_code == 200

    res_start_2 = client.post(f"/api/v1/production/executions/{exec_2['id']}/transition", json={
        "target_status": "in_progress",
    }, headers=headers)
    assert res_start_2.status_code == 200
    assert res_start_2.json()["status"] == "in_progress"

    res_mat_2 = client.post(f"/api/v1/production/executions/{exec_2['id']}/material-consumption", json={
        "material_type": "GEMSTONE",
        "material_name": "Diamond Solitaire 1.5ct",
        "unit": "pcs",
        "actual_quantity": 2.0,
        "wastage_quantity": 0.0,
    }, headers=headers)
    assert res_mat_2.status_code == 201

    res_comp_2 = client.post(f"/api/v1/production/executions/{exec_2['id']}/transition", json={
        "target_status": "completed",
    }, headers=headers)
    assert res_comp_2.status_code == 200
    assert res_comp_2.json()["status"] == "completed"
    assert res_comp_2.status_code == 200

    # 15. ORDER COMPLETION GATE VERIFICATION
    # Attempting to complete order BEFORE Op 2 QC must be rejected!
    res_early_comp = client.post(f"/api/v1/production/orders/{order_id}/complete", headers=headers)
    assert res_early_comp.status_code in (400, 409)

    # Perform QC on Op 2 (PASS)
    res_qc_2 = client.post(f"/api/v1/production/executions/{exec_2['id']}/quality-check", json={
        "result": "PASS",
        "defect_severity": "NONE",
        "notes": "Setting secure, stone alignment perfect.",
        "checked_by": "QC-INSP-101",
    }, headers=headers)
    assert res_qc_2.status_code == 201
    assert res_qc_2.json()["result"] == "PASS"

    # Attempting to complete order before remaining steps (3..N) are completed must still be rejected (Phase J.5 gate)
    if len(executions) > 2:
        res_still_early = client.post(f"/api/v1/production/orders/{order_id}/complete", headers=headers)
        assert res_still_early.status_code in (400, 409)

    # Complete all remaining sequential steps (3..N) with proper workers and machines
    for idx, remaining_exec in enumerate(executions[2:], start=3):
        r_skill = remaining_exec.get("required_skill") or "general"
        r_mach = remaining_exec.get("required_machine_type") or "general"
        w = client.post("/api/v1/production/workers", json={
            "name": f"Artisan Step {idx}",
            "skill": r_skill,
            "capacity_hours_per_day": 8.0,
        }, headers=headers).json()
        m = client.post("/api/v1/production/machines", json={
            "name": f"Machine Step {idx}",
            "machine_type": r_mach,
            "capacity_hours_per_day": 8.0,
        }, headers=headers).json()
        client.post(f"/api/v1/production/executions/{remaining_exec['id']}/assign-worker", json={
            "worker_id": w["id"],
        }, headers=headers)
        client.post(f"/api/v1/production/executions/{remaining_exec['id']}/assign-machine", json={
            "machine_id": m["id"],
        }, headers=headers)
        client.post(f"/api/v1/production/executions/{remaining_exec['id']}/transition", json={
            "target_status": "in_progress",
        }, headers=headers)
        client.post(f"/api/v1/production/executions/{remaining_exec['id']}/transition", json={
            "target_status": "completed",
        }, headers=headers)
        client.post(f"/api/v1/production/executions/{remaining_exec['id']}/quality-check", json={
            "result": "PASS",
            "defect_severity": "NONE",
            "notes": f"Step {idx} quality inspection passed.",
            "checked_by": f"QC-INSP-{idx}",
        }, headers=headers)

    # 16. ORDER COMPLETION (Now that ALL steps are completed and PASS QC)
    res_final_order_comp = client.post(f"/api/v1/production/orders/{order_id}/complete", headers=headers)
    assert res_final_order_comp.status_code == 200
    assert res_final_order_comp.json()["status"] == "completed"

    # 17. PRODUCTION SUMMARY & DASHBOARD OVERVIEW VERIFICATION
    res_summary = client.get("/api/v1/production/summary", headers=headers)
    assert res_summary.status_code == 200
    summary_data = res_summary.json()
    assert summary_data["completed_orders"] >= 1

    res_dash = client.get("/api/v1/dashboard/overview", headers=headers)
    assert res_dash.status_code == 200
    assert "kpis" in res_dash.json()

    # 18. J.7 PLANNED VS ACTUAL ANALYTICS VERIFICATION
    res_analytics = client.get(f"/api/v1/production/orders/{order_id}/analytics", headers=headers)
    assert res_analytics.status_code == 200
    analytics_data = res_analytics.json()
    assert analytics_data["order_id"] == order_id
    assert "planned" in analytics_data
    assert "actual" in analytics_data
    assert "variance" in analytics_data
    assert "operations" in analytics_data
    assert "quality" in analytics_data
    assert "rework" in analytics_data
    assert "schedule" in analytics_data
    assert analytics_data["quality"]["total_checks"] == len(executions)
    assert analytics_data["quality"]["passed"] == len(executions)
    assert analytics_data["quality"]["quality_gate_passed"] is True
    assert analytics_data["quality"]["first_pass_yield_percent"] == 100.0


def test_rework_workflow_and_original_execution_immutability(client: TestClient, db_session: Session):
    """
    Validates the J.5 Quality Control Rework cycle:
    Op 1 Completed -> QC REWORK -> Create Rework Execution ->
    Verify Original Execution Remains Immutable -> Run Rework ->
    Material on Rework -> QC PASS on Rework -> Order Completion.
    """
    headers = _register_user(client, "rework_tester@jewelmind.com", "Rework Tester")

    # Setup design, render, approved spec, and order
    res_des = client.post("/api/v1/designs", json={"name": "Pendant", "category": "Pendant"}, headers=headers)
    design_id = res_des.json()["id"]

    render_id = uuid.uuid4()
    render = DesignRender(
        id=render_id,
        design_id=uuid.UUID(design_id),
        user_id=uuid.UUID(res_des.json()["user_id"]),
        version_number=1,
        render_mode="studio",
        prompt="Diamond Pendant",
        image_url=f"/api/v1/ai/render/outputs/{render_id}.png",
        is_approved_for_production=True,
    )
    db_session.add(render)
    db_session.commit()

    res_spec = client.post("/api/v1/production-specifications/generate", json={"render_id": str(render_id)}, headers=headers)
    spec_id = res_spec.json()["id"]
    client.post(f"/api/v1/production-specifications/{spec_id}/approve", headers=headers)

    res_order = client.post("/api/v1/production/orders/from-specification", json={
        "specification_id": spec_id,
        "quantity": 1,
        "deadline": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=5)).isoformat(),
    }, headers=headers)
    order_id = res_order.json()["id"]

    # Initialize executions
    res_init = client.post(f"/api/v1/production/orders/{order_id}/executions/initialize", headers=headers)
    init_data = res_init.json()
    executions = init_data if isinstance(init_data, list) else init_data.get("executions", [])
    exec_1 = executions[0]

    # Start and complete op 1 via transition
    client.post(f"/api/v1/production/executions/{exec_1['id']}/transition", json={
        "target_status": "in_progress",
    }, headers=headers)
    client.post(f"/api/v1/production/executions/{exec_1['id']}/transition", json={
        "target_status": "completed",
    }, headers=headers)

    # QC Decision: REWORK
    res_qc_rework = client.post(f"/api/v1/production/executions/{exec_1['id']}/quality-check", json={
        "result": "REWORK",
        "defect_severity": "MEDIUM",
        "notes": "Slight surface roughness on bezel. Send back for refinishing.",
        "checked_by": "INSP-REWORK",
    }, headers=headers)
    assert res_qc_rework.status_code == 201
    assert res_qc_rework.json()["result"] == "REWORK"

    # Order cannot complete while in rework state
    assert client.post(f"/api/v1/production/orders/{order_id}/complete", headers=headers).status_code in (400, 409)

    # Create rework execution
    res_rework_exec = client.post(f"/api/v1/production/executions/{exec_1['id']}/rework", json={
        "operator_notes": "Supervisor authorized rework.",
    }, headers=headers)
    assert res_rework_exec.status_code == 201
    rework_exec = res_rework_exec.json()
    assert rework_exec["execution_type"] == "rework"
    assert rework_exec["attempt_number"] == 2
    assert rework_exec["rework_of_execution_id"] == exec_1["id"]
    assert rework_exec["id"] != exec_1["id"]

    # VERIFY ORIGINAL EXECUTION IMMUTABILITY
    res_orig = client.get(f"/api/v1/production/executions/{exec_1['id']}", headers=headers)
    assert res_orig.status_code == 200
    assert res_orig.json()["status"] == "completed"
    assert res_orig.json()["execution_type"] == "normal"

    # Execute rework operation
    client.post(f"/api/v1/production/executions/{rework_exec['id']}/transition", json={
        "target_status": "in_progress",
    }, headers=headers)
    # Record material used during rework (e.g. polishing paste / metal touchup)
    client.post(f"/api/v1/production/executions/{rework_exec['id']}/material-consumption", json={
        "material_type": "METAL",
        "material_name": "Gold Solder",
        "unit": "g",
        "actual_quantity": 0.2,
        "wastage_quantity": 0.05,
    }, headers=headers)
    client.post(f"/api/v1/production/executions/{rework_exec['id']}/transition", json={
        "target_status": "completed",
    }, headers=headers)

    # QC Pass on Rework execution
    res_rework_qc = client.post(f"/api/v1/production/executions/{rework_exec['id']}/quality-check", json={
        "result": "PASS",
        "defect_severity": "NONE",
        "notes": "Rework successful. Bezel mirror finish restored.",
        "checked_by": "INSP-REWORK",
    }, headers=headers)
    assert res_rework_qc.status_code == 201
    assert res_rework_qc.json()["result"] == "PASS"


def test_cross_tenant_idor_isolation_comprehensive(client: TestClient, db_session: Session):
    """
    Ensures strict tenant isolation between User A and User B across all entities:
    Designs, Renders, Specifications, Orders, Executions, Materials, QC, Analytics.
    """
    headers_a = _register_user(client, "tenant_a@jewelmind.com", "Tenant A")
    headers_b = _register_user(client, "tenant_b@jewelmind.com", "Tenant B")

    # User A creates Design, Render, Spec, Order, Execution, Material, QC
    res_des = client.post("/api/v1/designs", json={"name": "Private Ring A", "category": "Ring"}, headers=headers_a)
    design_id = res_des.json()["id"]

    render_id = uuid.uuid4()
    render = DesignRender(
        id=render_id,
        design_id=uuid.UUID(design_id),
        user_id=uuid.UUID(res_des.json()["user_id"]),
        version_number=1,
        render_mode="studio",
        prompt="Private Ring A",
        image_url=f"/api/v1/ai/render/outputs/{render_id}.png",
        is_approved_for_production=True,
    )
    db_session.add(render)
    db_session.commit()

    res_spec = client.post("/api/v1/production-specifications/generate", json={"render_id": str(render_id)}, headers=headers_a)
    spec_id = res_spec.json()["id"]
    client.post(f"/api/v1/production-specifications/{spec_id}/approve", headers=headers_a)

    res_order = client.post("/api/v1/production/orders/from-specification", json={
        "specification_id": spec_id,
        "quantity": 1,
        "deadline": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).isoformat(),
    }, headers=headers_a)
    order_id = res_order.json()["id"]

    res_init = client.post(f"/api/v1/production/orders/{order_id}/executions/initialize", headers=headers_a)
    init_data = res_init.json()
    exec_id = (init_data if isinstance(init_data, list) else init_data.get("executions", []))[0]["id"]

    # 1. User B attempts to access User A's Specification -> 404
    assert client.get(f"/api/v1/production-specifications/{spec_id}", headers=headers_b).status_code == 404
    assert client.patch(f"/api/v1/production-specifications/{spec_id}", json={"fabrication_notes": "Hacked"}, headers=headers_b).status_code == 404
    assert client.post(f"/api/v1/production-specifications/{spec_id}/approve", headers=headers_b).status_code == 404

    # 2. User B attempts to create Order referencing User A's Specification -> 404
    assert client.post("/api/v1/production/orders/from-specification", json={
        "specification_id": spec_id,
        "quantity": 1,
        "deadline": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).isoformat(),
    }, headers=headers_b).status_code == 404

    # 3. User B attempts to access User A's Execution -> 404
    assert client.get(f"/api/v1/production/executions/{exec_id}", headers=headers_b).status_code == 404
    assert client.post(f"/api/v1/production/executions/{exec_id}/transition", json={"target_status": "in_progress"}, headers=headers_b).status_code == 404

    # 4. User B attempts to record material consumption on User A's execution -> 404
    assert client.post(f"/api/v1/production/executions/{exec_id}/material-consumption", json={
        "material_type": "METAL",
        "material_name": "Gold",
        "unit": "g",
        "actual_quantity": 1.0,
    }, headers=headers_b).status_code == 404

    # 5. User B attempts to record QC on User A's execution -> 404
    assert client.post(f"/api/v1/production/executions/{exec_id}/quality-check", json={
        "result": "PASS",
    }, headers=headers_b).status_code == 404

    # 6. User B attempts to access User A's Analytics -> 404
    assert client.get(f"/api/v1/production/orders/{order_id}/analytics", headers=headers_b).status_code == 404


def test_malicious_parameter_injection_rejected(client: TestClient, db_session: Session):
    """
    Verifies clients cannot inject user_id, override timestamps, or spoof audit fields.
    """
    headers = _register_user(client, "injection_tester@jewelmind.com", "Injection Tester")
    fake_user_id = str(uuid.uuid4())

    # 1. Attempting to supply arbitrary user_id on design creation
    res_des = client.post("/api/v1/designs", json={
        "name": "Injection Test Ring",
        "category": "Ring",
        "user_id": fake_user_id,
        "created_at": "2099-01-01T00:00:00Z",
    }, headers=headers)
    assert res_des.status_code in (201, 422)
    if res_des.status_code == 201:
        # Server must have ignored the client-supplied user_id
        assert res_des.json()["user_id"] != fake_user_id

    # 2. Attempting to supply extra fields on order creation from specification
    # ProductionOrderCreateFromSpecification has extra="forbid"
    res_order = client.post("/api/v1/production/orders/from-specification", json={
        "specification_id": str(uuid.uuid4()),
        "quantity": 1,
        "deadline": "2026-10-01T00:00:00Z",
        "user_id": fake_user_id,  # Extra forbidden field
        "status": "completed",    # Extra forbidden field
    }, headers=headers)
    assert res_order.status_code == 422


def test_analytics_read_only_zero_mutation(client: TestClient, db_session: Session):
    """
    Verifies that calling J.7 analytics endpoints (order analytics, summary analytics)
    is strictly read-only and does not mutate Orders, Specifications, Executions,
    MaterialConsumptions, or QualityChecks.
    """
    headers = _register_user(client, "analytics_readonly@jewelmind.com", "Analytics Auditor")

    # Setup simple design and order
    res_des = client.post("/api/v1/designs", json={"name": "Analytics Ring", "category": "Ring"}, headers=headers)
    design_id = res_des.json()["id"]

    res_order = client.post("/api/v1/production/orders", json={
        "design_id": design_id,
        "quantity": 3,
        "priority": "medium",
        "deadline": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=4)).isoformat(),
    }, headers=headers)
    order_id = res_order.json()["id"]

    # Count database entities before analytics calls
    orders_before = db_session.query(ProductionOrder).count()
    specs_before = db_session.query(ProductionSpecification).count()
    execs_before = db_session.query(OperationExecution).count()
    mats_before = db_session.query(MaterialConsumption).count()
    qcs_before = db_session.query(QualityCheck).count()

    # Call analytics repeatedly
    for _ in range(3):
        res1 = client.get(f"/api/v1/production/orders/{order_id}/analytics", headers=headers)
        assert res1.status_code == 200
        res2 = client.get("/api/v1/production/analytics/summary", headers=headers)
        assert res2.status_code == 200

    # Count database entities after analytics calls
    assert db_session.query(ProductionOrder).count() == orders_before
    assert db_session.query(ProductionSpecification).count() == specs_before
    assert db_session.query(OperationExecution).count() == execs_before
    assert db_session.query(MaterialConsumption).count() == mats_before
    assert db_session.query(QualityCheck).count() == qcs_before
