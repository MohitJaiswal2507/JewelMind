"""
Production Management API Router
Provides REST endpoints for Production Orders, Workshop Workers, Machines, and Aggregated Summary KPIs.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.production import (
    MachineCreate,
    MachineListResponse,
    MachineResponse,
    MachineUpdate,
    OrderPriority,
    OrderStatus,
    ProductionOrderCreate,
    ProductionOrderListResponse,
    ProductionOrderResponse,
    ProductionOrderUpdate,
    ProductionSummaryResponse,
    WorkerCreate,
    WorkerListResponse,
    WorkerResponse,
    WorkerUpdate,
)
from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    ProductionScheduleListResponse,
    ProductionScheduleResponse,
)
from app.services.production_service import production_service
from app.services.production_optimization_service import production_optimization_service

router = APIRouter(prefix="/production", tags=["Production Management"])


# ---------------------------------------------------------------------------
# Summary KPI Metrics
# ---------------------------------------------------------------------------

@router.get(
    "/summary",
    response_model=ProductionSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated production KPI metrics",
)
async def get_production_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns real-time deterministic metrics for active orders, overdue orders,
    artisan workshop capacity, and machine operational capacity.
    """
    return production_service.get_production_summary(db=db, user_id=current_user.id)


# ---------------------------------------------------------------------------
# Production Orders Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/orders",
    response_model=ProductionOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new production manufacturing order",
)
async def create_order(
    order_in: ProductionOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Creates a new production order linked to an existing, validated user design.
    """
    return production_service.create_order(
        db=db,
        user_id=current_user.id,
        order_in=order_in,
    )


@router.get(
    "/orders",
    response_model=ProductionOrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="List paginated production orders",
)
async def list_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filter by status"),
    priority_filter: Optional[OrderPriority] = Query(None, alias="priority", description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search keyword in design name or order notes"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns a paginated list of production orders for the authenticated user.
    """
    items, total, pages = production_service.get_user_orders(
        db=db,
        user_id=current_user.id,
        status=status_filter,
        priority=priority_filter,
        search=search,
        page=page,
        page_size=page_size,
    )
    return ProductionOrderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/orders/{order_id}",
    response_model=ProductionOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a specific production order by ID",
)
async def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves production order details with associated design information.
    """
    return production_service.get_order_by_id(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
    )


@router.put(
    "/orders/{order_id}",
    response_model=ProductionOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a production order",
)
@router.patch(
    "/orders/{order_id}",
    response_model=ProductionOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a production order",
)
async def update_order(
    order_id: uuid.UUID,
    order_in: ProductionOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Updates production order parameters (quantity, priority, status, deadline, notes).
    """
    return production_service.update_order(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
        order_in=order_in,
    )


@router.delete(
    "/orders/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a production order",
)
async def delete_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deletes a production order from the workspace.
    """
    production_service.delete_order(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Workers Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/workers",
    response_model=WorkerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new workshop artisan / worker",
)
async def create_worker(
    worker_in: WorkerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Registers a new artisan worker with primary craft skill and daily working capacity.
    """
    return production_service.create_worker(
        db=db,
        user_id=current_user.id,
        worker_in=worker_in,
    )


@router.get(
    "/workers",
    response_model=WorkerListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all workshop workers",
)
async def list_workers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Lists all workshop workers registered by the authenticated user.
    """
    items = production_service.get_user_workers(db=db, user_id=current_user.id)
    return WorkerListResponse(items=items, total=len(items))


@router.get(
    "/workers/{worker_id}",
    response_model=WorkerResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve worker details by ID",
)
async def get_worker(
    worker_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves detailed artisan information.
    """
    return production_service.get_worker_by_id(
        db=db,
        user_id=current_user.id,
        worker_id=worker_id,
    )


@router.put(
    "/workers/{worker_id}",
    response_model=WorkerResponse,
    status_code=status.HTTP_200_OK,
    summary="Update worker details or availability",
)
@router.patch(
    "/workers/{worker_id}",
    response_model=WorkerResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update worker details or availability",
)
async def update_worker(
    worker_id: uuid.UUID,
    worker_in: WorkerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Updates worker craft skill, availability toggle, or daily capacity hours.
    """
    return production_service.update_worker(
        db=db,
        user_id=current_user.id,
        worker_id=worker_id,
        worker_in=worker_in,
    )


@router.delete(
    "/workers/{worker_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a worker",
)
async def delete_worker(
    worker_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deletes an artisan worker record.
    """
    production_service.delete_worker(
        db=db,
        user_id=current_user.id,
        worker_id=worker_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Machines Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/machines",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new workshop machine / equipment",
)
async def create_machine(
    machine_in: MachineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Registers specialized manufacturing machinery (laser engraver, 3D printer, furnace, etc.).
    """
    return production_service.create_machine(
        db=db,
        user_id=current_user.id,
        machine_in=machine_in,
    )


@router.get(
    "/machines",
    response_model=MachineListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all workshop machines",
)
async def list_machines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Lists all machinery and equipment registered by the authenticated user.
    """
    items = production_service.get_user_machines(db=db, user_id=current_user.id)
    return MachineListResponse(items=items, total=len(items))


@router.get(
    "/machines/{machine_id}",
    response_model=MachineResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve machine details by ID",
)
async def get_machine(
    machine_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves detailed machine information.
    """
    return production_service.get_machine_by_id(
        db=db,
        user_id=current_user.id,
        machine_id=machine_id,
    )


@router.put(
    "/machines/{machine_id}",
    response_model=MachineResponse,
    status_code=status.HTTP_200_OK,
    summary="Update machine details or operational status",
)
@router.patch(
    "/machines/{machine_id}",
    response_model=MachineResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update machine details or operational status",
)
async def update_machine(
    machine_id: uuid.UUID,
    machine_in: MachineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Updates machine type, capacity hours, or active status.
    """
    return production_service.update_machine(
        db=db,
        user_id=current_user.id,
        machine_id=machine_id,
        machine_in=machine_in,
    )


@router.delete(
    "/machines/{machine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a machine",
)
async def delete_machine(
    machine_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deletes a machine record.
    """
    production_service.delete_machine(
        db=db,
        user_id=current_user.id,
        machine_id=machine_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Production Optimization & Scheduling Endpoints (OR-Tools CP-SAT)
# ---------------------------------------------------------------------------

@router.post(
    "/optimize",
    response_model=OptimizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run OR-Tools CP-SAT production scheduling optimization",
)
async def optimize_production(
    request: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generates an optimized, conflict-free production schedule for the user's
    production orders respecting worker skills, machine capacities, deadlines,
    and priority weights using Google OR-Tools CP-SAT.
    """
    return production_optimization_service.optimize(
        db=db,
        user_id=current_user.id,
        request=request,
    )


@router.get(
    "/schedules",
    response_model=ProductionScheduleListResponse,
    status_code=status.HTTP_200_OK,
    summary="List saved production schedules",
)
async def list_schedules(
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves paginated historical production schedules generated for the user.
    """
    return production_optimization_service.get_user_schedules(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/schedules/{schedule_id}",
    response_model=ProductionScheduleResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a specific production schedule with full task breakdown",
)
async def get_schedule(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves full details and timeline task records for a saved production schedule.
    """
    return production_optimization_service.get_schedule_by_id(
        db=db,
        user_id=current_user.id,
        schedule_id=schedule_id,
    )


@router.delete(
    "/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved production schedule",
)
async def delete_schedule(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deletes a saved production schedule and cascades to its task allocations.
    """
    production_optimization_service.delete_schedule(
        db=db,
        user_id=current_user.id,
        schedule_id=schedule_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
