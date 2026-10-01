"""
Production Execution API Router
Provides authenticated REST endpoints for initializing, inspecting, and transitioning
actual shop-floor manufacturing operations (OperationExecution).
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.execution import (
    MachineAssignmentRequest,
    MaterialConsumptionCreate,
    MaterialConsumptionResponse,
    OperationExecutionCreate,
    OperationExecutionListResponse,
    OperationExecutionResponse,
    OperationExecutionTransitionRequest,
    OrderMaterialSummaryResponse,
    OrderQualitySummaryResponse,
    QualityCheckCreate,
    QualityCheckResponse,
    ReworkExecutionCreate,
    WorkerAssignmentRequest,
)
from app.services.production_execution_service import (
    production_execution_service,
    serialize_execution_response,
)

router = APIRouter(prefix="/production", tags=["Production Execution"])


@router.post(
    "/orders/{order_id}/executions/initialize",
    response_model=List[OperationExecutionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Initialize shop-floor execution records for a production order",
    description=(
        "Initializes sequential OperationExecution records from the authoritative routing steps "
        "defined in the order's approved Production Specification. Sets Step 1 to READY and subsequent "
        "steps to PENDING. If matching CP-SAT ScheduledTasks exist, planned schedule intervals are linked. "
        "Idempotent: will not create duplicate executions if already initialized."
    ),
)
async def initialize_order_executions(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Initializes execution records for a spec-backed production order.
    Enforces multi-tenant ownership and specification validation.
    """
    executions = production_execution_service.initialize_order_executions(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
    )
    return [serialize_execution_response(e) for e in executions]


@router.get(
    "/orders/{order_id}/executions",
    response_model=OperationExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all operation executions for a production order",
    description="Returns all shop-floor operation execution records for an order, ordered by routing step number.",
)
async def list_order_executions(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves execution records for a production order. Enforces tenant isolation.
    """
    return production_execution_service.get_order_execution_list_response(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
    )


@router.get(
    "/executions/{execution_id}",
    response_model=OperationExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve single operation execution details",
    description="Retrieves full shop-floor execution details including planned vs actual timing, pause duration, and notes.",
)
async def get_execution(
    execution_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves execution record by ID. Enforces multi-tenant ownership.
    """
    execution = production_execution_service.get_execution_by_id(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
    )
    return serialize_execution_response(execution)


@router.post(
    "/executions/{execution_id}/assign-worker",
    response_model=OperationExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign an eligible artisan to an operation execution",
    description=(
        "Assigns a workshop artisan to a READY, PENDING, or BLOCKED operation. "
        "Validates multi-tenant ownership, artisan presence/availability, and skill eligibility. "
        "Rejects assignment to COMPLETED operations or reassignment while IN_PROGRESS or PAUSED."
    ),
)
async def assign_worker(
    execution_id: uuid.UUID,
    payload: WorkerAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Assigns an eligible artisan to an execution record. Enforces skill matching and tenant isolation.
    """
    execution = production_execution_service.assign_worker(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
        worker_id=payload.worker_id,
    )
    return serialize_execution_response(execution)


@router.post(
    "/executions/{execution_id}/assign-machine",
    response_model=OperationExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign compatible equipment to an operation execution",
    description=(
        "Assigns workshop equipment to a READY, PENDING, or BLOCKED operation. "
        "Validates multi-tenant ownership, equipment operational status, and type compatibility. "
        "Rejects assignment to COMPLETED operations or reassignment while IN_PROGRESS or PAUSED."
    ),
)
async def assign_machine(
    execution_id: uuid.UUID,
    payload: MachineAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Assigns compatible equipment to an execution record. Enforces machine compatibility and tenant isolation.
    """
    execution = production_execution_service.assign_machine(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
        machine_id=payload.machine_id,
    )
    return serialize_execution_response(execution)


@router.post(
    "/executions/{execution_id}/transition",
    response_model=OperationExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Transition operation execution state on the shop floor",
    description=(
        "Executes a state transition (e.g. READY -> IN_PROGRESS, IN_PROGRESS -> PAUSED, "
        "PAUSED -> IN_PROGRESS, IN_PROGRESS -> COMPLETED). Validates state machine rules, "
        "records actual start/end timestamps, calculates net bench duration, audits notes, "
        "and enforces artisan skill eligibility, equipment compatibility, and conflict prevention."
    ),
)
async def transition_execution(
    execution_id: uuid.UUID,
    request_in: OperationExecutionTransitionRequest,
    validate_resources: Optional[bool] = Query(
        None,
        description="Optional override to strictly enforce or bypass required worker/machine checks on start",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Transitions an operation execution. Enforces strict state-machine rules, immutability,
    predecessor completion, and worker/machine execution eligibility (Phase J.3).
    """
    resolved_val = validate_resources if validate_resources is not None else request_in.validate_resources
    execution = production_execution_service.transition_execution(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
        req=request_in,
        validate_resources=resolved_val,
    )
    return serialize_execution_response(execution)


@router.post(
    "/executions",
    response_model=OperationExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Directly create an operation execution record",
    description="Creates a single execution record with strict verification of step-order-specification linkage.",
)
async def create_execution(
    create_in: OperationExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Creates an operation execution record directly.
    """
    execution = production_execution_service.create_execution(
        db=db,
        user_id=current_user.id,
        create_in=create_in,
    )
    return serialize_execution_response(execution)


# =========================================================================
# Phase J.4: Material Consumption & Wastage Tracking Endpoints
# =========================================================================

@router.post(
    "/executions/{execution_id}/material-consumption",
    response_model=MaterialConsumptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record actual material consumption against an operation execution",
    description=(
        "Records what material was actually consumed and wasted during a shop-floor operation execution. "
        "Distinguishes planned baseline from actual usage and scrap. Validates execution state (IN_PROGRESS "
        "or COMPLETED only), quantity constraints, and authoritative specification item alignment."
    ),
)
async def record_material_consumption(
    execution_id: uuid.UUID,
    payload: MaterialConsumptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Records actual material consumption for an execution step. Enforces tenant ownership
    and prevents modifying the authoritative specification baseline or CP-SAT schedule.
    """
    return production_execution_service.record_material_consumption(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
        payload=payload,
    )


@router.get(
    "/executions/{execution_id}/material-consumption",
    response_model=List[MaterialConsumptionResponse],
    status_code=status.HTTP_200_OK,
    summary="List material consumption records for an operation execution",
    description="Returns all actual material consumption and wastage records recorded for a specific operation execution.",
)
async def list_execution_material_consumptions(
    execution_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves material consumption records for an execution step. Enforces tenant isolation.
    """
    return production_execution_service.get_execution_material_consumptions(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
    )


@router.get(
    "/orders/{order_id}/material-consumption",
    response_model=List[MaterialConsumptionResponse],
    status_code=status.HTTP_200_OK,
    summary="List all material consumption records for a production order",
    description="Returns all actual material consumption records across all execution steps for a production order.",
)
async def list_order_material_consumptions(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves all material consumption records for an entire production order. Enforces tenant isolation.
    """
    return production_execution_service.get_order_material_consumptions(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
    )


@router.get(
    "/orders/{order_id}/material-summary",
    response_model=OrderMaterialSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get planned vs actual material consumption summary for an order",
    description=(
        "Returns a concise summary comparing planned quantity, actual consumed quantity, "
        "and wastage quantity grouped by material identity/type for a production order."
    ),
)
async def get_order_material_summary(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves concise material summary for an order. Enforces multi-tenant isolation.
    """
    return production_execution_service.get_order_material_summary(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
    )


# =========================================================================
# Phase J.5: Quality Control & Controlled Rework Endpoints
# =========================================================================

@router.post(
    "/executions/{execution_id}/quality-check",
    response_model=QualityCheckResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record quality control inspection result for an operation execution",
    description=(
        "Records an append-only quality check outcome (PASS, FAIL, REWORK) against a COMPLETED "
        "operation execution. Strictly derives user, order, step, and inspection timestamps server-side. "
        "Enforces tenant ownership and automatically evaluates the order completion quality gate."
    ),
)
async def record_quality_check(
    execution_id: uuid.UUID,
    payload: QualityCheckCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Records a quality inspection result for an execution step. Enforces tenant ownership
    and validates that the execution is COMPLETED.
    """
    return production_execution_service.record_quality_check(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
        payload=payload,
    )


@router.get(
    "/executions/{execution_id}/quality-check",
    response_model=List[QualityCheckResponse],
    status_code=status.HTTP_200_OK,
    summary="Get quality check history for an operation execution",
    description="Returns chronological inspection records for a specific operation execution, ordered newest first.",
)
async def get_execution_quality_checks(
    execution_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves QC history for an execution step. Enforces multi-tenant isolation.
    """
    return production_execution_service.get_execution_quality_checks(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
    )


@router.post(
    "/executions/{execution_id}/rework",
    response_model=OperationExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Authorize and initialize controlled rework execution",
    description=(
        "Initializes a new rework OperationExecution following a REWORK quality check outcome. "
        "Preserves the original execution historically in COMPLETED state and begins the rework "
        "execution in READY state, ready for artisan/equipment allocation and material tracking."
    ),
)
async def create_rework_execution(
    execution_id: uuid.UUID,
    payload: Optional[ReworkExecutionCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Initializes a controlled rework execution. Enforces multi-tenant ownership and REWORK QC validation.
    """
    rework_ex = production_execution_service.create_rework_execution(
        db=db,
        user_id=current_user.id,
        execution_id=execution_id,
        payload=payload,
    )
    return serialize_execution_response(rework_ex)


@router.get(
    "/orders/{order_id}/quality-checks",
    response_model=OrderQualitySummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get order quality summary and gate status",
    description=(
        "Returns authoritative quality summary metrics for all routing operations in a production order, "
        "including total operations, passed, failed, rework, pending inspections, and quality gate status."
    ),
)
async def get_order_quality_summary(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves concise quality gate summary for a production order. Enforces multi-tenant isolation.
    """
    return production_execution_service.get_order_quality_summary(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
    )


@router.post(
    "/orders/{order_id}/complete",
    status_code=status.HTTP_200_OK,
    summary="Explicitly complete production order with quality gate verification",
    description=(
        "Validates that all manufacturing routing operations for an order are finished and have "
        "100% PASS quality check outcomes. Rejects with 409 if any operation is pending, failed, "
        "under rework, or uninspected."
    ),
)
async def complete_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Explicitly completes a production order upon satisfying the Phase J.5 Quality Control gate.
    """
    order = production_execution_service.complete_order(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
    )
    return {
        "order_id": str(order.id),
        "status": order.status,
        "message": "Production order successfully completed with verified quality gate.",
    }

