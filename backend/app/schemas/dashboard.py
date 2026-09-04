"""
Dashboard Aggregated Schemas for JewelMind Phase 13.
Provides comprehensive type definitions for multi-subsystem executive analytics.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class DashboardUserSummary(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class DashboardKpis(BaseModel):
    total_designs: int = 0
    active_designs: int = 0
    draft_designs: int = 0
    rendered_designs: int = 0
    total_orders: int = 0
    pending_orders: int = 0
    in_progress_orders: int = 0
    completed_orders: int = 0
    overdue_orders: int = 0
    total_workers: int = 0
    available_workers: int = 0
    total_worker_capacity_hours: float = 0.0
    total_machines: int = 0
    available_machines: int = 0
    total_machine_capacity_hours: float = 0.0
    workshop_utilization_pct: float = 0.0
    on_time_delivery_rate: float = 100.0


class DistributionItem(BaseModel):
    name: str
    count: int
    percentage: float


class DashboardRecentAsset(BaseModel):
    id: UUID
    name: str
    category: str
    status: str
    sketch_image_url: Optional[str] = None
    rendered_image_url: Optional[str] = None
    ai_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DashboardDeadlineOrder(BaseModel):
    id: UUID
    design_id: UUID
    design_name: Optional[str] = None
    design_category: Optional[str] = None
    design_thumbnail_url: Optional[str] = None
    quantity: int
    priority: str
    status: str
    deadline: datetime
    is_overdue: bool


class DashboardLatestSchedule(BaseModel):
    id: UUID
    name: str
    solver_status: str
    makespan_hours: float
    total_orders_scheduled: int
    total_orders_unscheduled: int
    worker_utilization_pct: float
    machine_utilization_pct: float
    horizon_days: int
    runtime_seconds: float
    created_at: datetime


class SystemHealthStatus(BaseModel):
    backend: str = "online"
    database: str = "connected"
    ai_services: str = "ready"
    active_gpu: str = "RTX 4060 / Local PyTorch"


class DashboardOverviewResponse(BaseModel):
    user: DashboardUserSummary
    kpis: DashboardKpis
    categories: List[DistributionItem] = Field(default_factory=list)
    statuses: List[DistributionItem] = Field(default_factory=list)
    priorities: List[DistributionItem] = Field(default_factory=list)
    recent_designs: List[DashboardRecentAsset] = Field(default_factory=list)
    recent_renders: List[DashboardRecentAsset] = Field(default_factory=list)
    upcoming_deadlines: List[DashboardDeadlineOrder] = Field(default_factory=list)
    latest_schedule: Optional[DashboardLatestSchedule] = None
    system_status: SystemHealthStatus
