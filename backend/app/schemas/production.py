"""
Pydantic Schemas for Production Management (Orders, Workers, Machines, Capacity, and Summary)
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class OrderStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkerSkill(str, Enum):
    CAD_DESIGN = "cad_design"
    CASTING = "casting"
    STONE_SETTING = "stone_setting"
    POLISHING = "polishing"
    ENGRAVING = "engraving"
    GENERAL = "general"


class MachineType(str, Enum):
    LASER_ENGRAVER = "laser_engraver"
    WAX_3D_PRINTER = "3d_wax_printer"
    CASTING_FURNACE = "casting_furnace"
    CNC_MILLING = "cnc_milling"
    ULTRASONIC_CLEANER = "ultrasonic_cleaner"
    POLISHING_LATHE = "polishing_lathe"
    GENERAL = "general"


# ---------------------------------------------------------------------------
# Production Order Schemas
# ---------------------------------------------------------------------------

class ProductionOrderBase(BaseModel):
    design_id: uuid.UUID = Field(..., description="ID of the associated jewellery design")
    quantity: int = Field(default=1, gt=0, description="Quantity of items to manufacture (> 0)")
    priority: OrderPriority = Field(default=OrderPriority.MEDIUM, description="Production priority level")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Production lifecycle status")
    deadline: datetime = Field(..., description="Target completion deadline timestamp (UTC)")
    notes: Optional[str] = Field(None, max_length=2000, description="Special artisan notes or production instructions")
    render_id: Optional[uuid.UUID] = Field(None, description="Optional ID of specific approved render")
    approved_render_url: Optional[str] = Field(None, description="Snapshot URL of approved render visual")
    specification_id: Optional[uuid.UUID] = Field(None, description="Optional ID of associated production specification")

    @field_validator("quantity")
    @classmethod
    def validate_quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be a positive integer greater than zero.")
        return v


class ProductionOrderCreate(ProductionOrderBase):
    pass


class ProductionOrderCreateFromSpecification(BaseModel):
    """Payload to create an authoritative ProductionOrder from an approved ProductionSpecification."""
    specification_id: uuid.UUID = Field(..., description="ID of the approved production specification")
    quantity: int = Field(default=1, gt=0, description="Quantity of items to manufacture (> 0)")
    priority: OrderPriority = Field(default=OrderPriority.MEDIUM, description="Production priority level")
    deadline: datetime = Field(..., description="Target completion deadline timestamp (UTC)")
    notes: Optional[str] = Field(None, max_length=2000, description="Special artisan notes or production instructions")

    model_config = ConfigDict(extra="forbid")

    @field_validator("quantity")
    @classmethod
    def validate_quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be a positive integer greater than zero.")
        return v


class ProductionOrderUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0, description="Updated manufacturing quantity")
    priority: Optional[OrderPriority] = None
    status: Optional[OrderStatus] = None
    deadline: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=2000)
    render_id: Optional[uuid.UUID] = None
    approved_render_url: Optional[str] = None
    specification_id: Optional[uuid.UUID] = None

    @field_validator("quantity")
    @classmethod
    def validate_quantity_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Quantity must be a positive integer greater than zero.")
        return v


class ProductionOrderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    design_id: uuid.UUID
    quantity: int
    priority: OrderPriority
    status: OrderStatus
    deadline: datetime
    notes: Optional[str] = None
    render_id: Optional[uuid.UUID] = None
    approved_render_url: Optional[str] = None
    specification_id: Optional[uuid.UUID] = None
    specification_version: Optional[int] = Field(None, description="Version number of the associated specification")
    specification_category: Optional[str] = Field(None, description="Category of the associated specification")
    routing_steps_count: Optional[int] = Field(None, description="Number of manufacturing operations in routing")
    materials_count: Optional[int] = Field(None, description="Number of material line items in BOM")
    gemstones_count: Optional[int] = Field(None, description="Number of gemstone requirements in BOM")
    is_overdue: bool = Field(default=False, description="Calculated flag indicating if deadline has passed while active")
    design_name: Optional[str] = Field(None, description="Name of the associated design")
    design_category: Optional[str] = Field(None, description="Category of the associated design")
    design_thumbnail_url: Optional[str] = Field(None, description="Preview image of the associated design")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



class ProductionOrderListResponse(BaseModel):
    items: List[ProductionOrderResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Worker Schemas
# ---------------------------------------------------------------------------

class WorkerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name of workshop artisan")
    skill: str = Field(default="general", max_length=100, description="Primary jewellery craft specialization")
    capacity_hours_per_day: float = Field(default=8.0, ge=0.0, le=24.0, description="Productive working hours available per day")
    is_available: bool = Field(default=True, description="Active workshop presence status")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Worker name cannot be blank or whitespace only.")
        return trimmed

    @field_validator("capacity_hours_per_day")
    @classmethod
    def validate_capacity_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Worker capacity hours per day must be non-negative (>= 0).")
        return round(v, 2)


class WorkerCreate(WorkerBase):
    pass


class WorkerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    skill: Optional[str] = Field(None, max_length=100)
    capacity_hours_per_day: Optional[float] = Field(None, ge=0.0, le=24.0)
    is_available: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Worker name cannot be blank or whitespace only.")
            return trimmed
        return v

    @field_validator("capacity_hours_per_day")
    @classmethod
    def validate_capacity_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0:
                raise ValueError("Worker capacity hours per day must be non-negative (>= 0).")
            return round(v, 2)
        return v


class WorkerResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    skill: str
    capacity_hours_per_day: float
    is_available: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkerListResponse(BaseModel):
    items: List[WorkerResponse]
    total: int


# ---------------------------------------------------------------------------
# Machine Schemas
# ---------------------------------------------------------------------------

class MachineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Machine model or workshop identifier")
    machine_type: str = Field(default="general", max_length=100, description="Equipment functional category")
    capacity_hours_per_day: float = Field(default=8.0, ge=0.0, le=24.0, description="Operational machine capacity per day (hours)")
    is_available: bool = Field(default=True, description="Operating / operational status")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Machine name cannot be blank or whitespace only.")
        return trimmed

    @field_validator("capacity_hours_per_day")
    @classmethod
    def validate_capacity_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Machine capacity hours per day must be non-negative (>= 0).")
        return round(v, 2)


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    machine_type: Optional[str] = Field(None, max_length=100)
    capacity_hours_per_day: Optional[float] = Field(None, ge=0.0, le=24.0)
    is_available: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Machine name cannot be blank or whitespace only.")
            return trimmed
        return v

    @field_validator("capacity_hours_per_day")
    @classmethod
    def validate_capacity_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0:
                raise ValueError("Machine capacity hours per day must be non-negative (>= 0).")
            return round(v, 2)
        return v


class MachineResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    machine_type: str
    capacity_hours_per_day: float
    is_available: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MachineListResponse(BaseModel):
    items: List[MachineResponse]
    total: int


# ---------------------------------------------------------------------------
# Dashboard / Summary Metrics
# ---------------------------------------------------------------------------

class ProductionSummaryResponse(BaseModel):
    total_orders: int = 0
    pending_orders: int = 0
    in_progress_orders: int = 0
    completed_orders: int = 0
    cancelled_orders: int = 0
    overdue_orders: int = 0
    total_workers: int = 0
    available_workers: int = 0
    total_worker_capacity_hours: float = 0.0
    total_machines: int = 0
    available_machines: int = 0
    total_machine_capacity_hours: float = 0.0
