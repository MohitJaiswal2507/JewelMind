"""
Production Optimization & Scheduling Pydantic Schemas
Defines request, response, metric, and task models for OR-Tools CP-SAT scheduler.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SolverStatusEnum(str, Enum):
    """CP-SAT Solver resolution status."""
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    MODEL_INVALID = "MODEL_INVALID"
    UNKNOWN = "UNKNOWN"


class OptimizationRequest(BaseModel):
    """Request payload to initiate CP-SAT production scheduling optimization."""
    order_ids: Optional[List[uuid.UUID]] = Field(
        default=None,
        description="Optional list of specific ProductionOrder UUIDs to schedule. If omitted, all pending and in-progress orders are included.",
    )
    start_date: Optional[datetime] = Field(
        default=None,
        description="Schedule start timestamp in UTC (defaults to current time).",
    )
    horizon_days: int = Field(
        default=14,
        ge=1,
        le=90,
        description="Optimization planning horizon in days (1 to 90 days).",
    )
    time_limit_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Maximum solver execution time limit in seconds (1 to 60s).",
    )
    persist_schedule: bool = Field(
        default=True,
        description="Whether to persist the generated schedule and tasks in the database.",
    )
    schedule_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Custom name for the persisted production schedule.",
    )


class ScheduledTaskResponse(BaseModel):
    """Detailed allocation record for a single manufacturing task."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    order_id: uuid.UUID
    design_id: Optional[uuid.UUID] = None
    design_name: Optional[str] = None
    design_image_url: Optional[str] = None
    quantity: int = 1
    priority: str = "medium"
    worker_id: Optional[uuid.UUID] = None
    worker_name: Optional[str] = None
    worker_skill: Optional[str] = None
    machine_id: Optional[uuid.UUID] = None
    machine_name: Optional[str] = None
    machine_type: Optional[str] = None
    operation_name: str
    start_time: datetime
    end_time: datetime
    duration_hours: float
    sequence_order: int = 1
    is_overdue: bool = False


class OptimizationMetrics(BaseModel):
    """Calculated key performance indicators and solver runtime statistics."""
    makespan_hours: float = 0.0
    total_orders_scheduled: int = 0
    total_orders_unscheduled: int = 0
    worker_utilization_pct: float = 0.0
    machine_utilization_pct: float = 0.0
    orders_on_time: int = 0
    orders_overdue: int = 0
    solver_runtime_ms: float = 0.0


class OptimizationResponse(BaseModel):
    """Top-level response payload returned by the optimization service & endpoint."""
    status: str = Field(description="'success', 'feasible', 'infeasible', or 'error'")
    solver_status: SolverStatusEnum
    message: str
    schedule: List[ScheduledTaskResponse] = []
    unscheduled_order_ids: List[uuid.UUID] = []
    metrics: OptimizationMetrics
    infeasibility_reasons: List[str] = []
    schedule_id: Optional[uuid.UUID] = None


class ProductionScheduleResponse(BaseModel):
    """Saved production schedule entity with nested task records."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    start_date: datetime
    horizon_days: int
    solver_status: str
    makespan_hours: float
    total_orders_scheduled: int
    total_orders_unscheduled: int
    worker_utilization_pct: float
    machine_utilization_pct: float
    runtime_seconds: float
    tasks: List[ScheduledTaskResponse] = []
    created_at: datetime
    updated_at: datetime


class ProductionScheduleListResponse(BaseModel):
    """Paginated collection of historical production schedules."""
    items: List[ProductionScheduleResponse]
    total: int
