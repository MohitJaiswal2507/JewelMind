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
    OperationExecutionCreate,
    OperationExecutionListResponse,
    OperationExecutionResponse,
    OperationExecutionTransitionRequest,
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
