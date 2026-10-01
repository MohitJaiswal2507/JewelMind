"""
Planned vs Actual Production Analytics Schemas (Phase J.7).
Provides deterministic data structures for order-level and atelier-wide
planned vs actual time, material, routing, quality, and schedule analytics.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class MaterialVarianceItem(BaseModel):
    """Variance analysis for a single material line item."""
    model_config = ConfigDict(from_attributes=True)

    material_type: str
    material_name: str
    unit: str
    planned_quantity: float
    actual_quantity: float
    wastage_quantity: float
    net_consumed_quantity: float
    variance_quantity: float = Field(
        ...,
        description="actual_quantity - planned_quantity"
    )
    material_variance: float = Field(
        ...,
        description="actual_quantity - planned_quantity (prompt alias)"
    )
    variance_percent: Optional[float] = Field(
        None,
        description="((actual_quantity - planned_quantity) / planned_quantity) * 100 if planned_quantity > 0 else None"
    )
    wastage_percent: Optional[float] = Field(
        None,
        description="(wastage_quantity / actual_quantity) * 100 if actual_quantity > 0 else None"
    )


class PlannedOrderAnalytics(BaseModel):
    """Authoritative planned production metrics derived from specification and schedule."""
    model_config = ConfigDict(from_attributes=True)

    quantity: int
    hours: float = Field(..., description="Sum of planned routing step hours for the order quantity")
    materials: List[MaterialVarianceItem] = Field(default_factory=list)


class ActualOrderAnalytics(BaseModel):
    """Actual shop-floor execution metrics recorded by artisans and QC inspectors."""
    model_config = ConfigDict(from_attributes=True)

    hours: float = Field(..., description="Sum of actual net operation execution durations")
    materials: List[MaterialVarianceItem] = Field(default_factory=list)


class VarianceOrderAnalytics(BaseModel):
    """Deterministic difference between actual and planned execution metrics."""
    model_config = ConfigDict(from_attributes=True)

    hours: float = Field(..., description="actual_hours - planned_hours")
    hours_percent: Optional[float] = Field(
        None,
        description="((actual_hours - planned_hours) / planned_hours) * 100 if planned_hours > 0 else None"
    )
    materials: List[MaterialVarianceItem] = Field(default_factory=list)


class OperationsOrderAnalytics(BaseModel):
    """Execution status distribution across routing steps."""
    model_config = ConfigDict(from_attributes=True)

    total: int
    completed: int
    in_progress: int
    paused: int
    blocked: int
    ready: int
    pending: int
    completion_rate_percent: float


class QualityOrderAnalytics(BaseModel):
    """Quality control verdict distribution and quality gate status."""
    model_config = ConfigDict(from_attributes=True)

    total_checks: int
    passed: int
    failed: int
    rework: int
    pending_quality_checks: int
    quality_gate_passed: bool
    first_pass_yield_percent: Optional[float] = None


class ReworkOrderAnalytics(BaseModel):
    """Controlled rework occurrences and rate."""
    model_config = ConfigDict(from_attributes=True)

    count: int = Field(..., description="Number of rework executions authorized")
    rate_percent: float = Field(..., description="(rework_count / total routing operations) * 100")


class ScheduleOrderAnalytics(BaseModel):
    """Planned vs actual milestone timing and schedule variance."""
    model_config = ConfigDict(from_attributes=True)

    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    deadline: Optional[datetime] = None
    schedule_variance_hours: Optional[float] = Field(
        None,
        description="Difference between actual completion/now and planned end (positive = delayed, negative = early)"
    )
    is_overdue: bool = False


class ProductionOrderAnalyticsResponse(BaseModel):
    """Authoritative response schema for an individual production order's planned vs actual analytics."""
    model_config = ConfigDict(from_attributes=True)

    order_id: UUID
    design_id: UUID
    design_name: Optional[str] = None
    status: str
    priority: str
    planned: PlannedOrderAnalytics
    actual: ActualOrderAnalytics
    variance: VarianceOrderAnalytics
    operations: OperationsOrderAnalytics
    quality: QualityOrderAnalytics
    rework: ReworkOrderAnalytics
    schedule: ScheduleOrderAnalytics


class AtelierAnalyticsSummaryResponse(BaseModel):
    """Cross-order aggregate analytics summary across the workshop."""
    model_config = ConfigDict(from_attributes=True)

    total_orders_analyzed: int
    active_orders_count: int
    completed_orders_count: int
    total_planned_hours: float
    total_actual_hours: float
    net_time_variance_hours: float
    average_time_variance_percent: Optional[float] = None
    total_rework_executions: int
    overall_rework_rate_percent: float
    total_qc_checks: int
    overall_qc_pass_rate_percent: Optional[float] = None
    orders_with_rework_count: int
    orders_quality_gate_passed_count: int
