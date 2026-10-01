"""
Pydantic Schemas for Production Execution (Shop-Floor Operation Tracking)
Enforces strict client input validation, forbidding client-controlled timestamps
or tenant/audit fields, while providing structured execution state contracts.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExecutionStatus(str, Enum):
    """
    Controlled states for shop-floor manufacturing operations.
    - PENDING: Predecessor operation is not yet completed.
    - READY: Operation is unblocked and available to begin.
    - IN_PROGRESS: Artisan has actively started the bench operation.
    - PAUSED: Operation temporarily halted (e.g. shift change, tool wait).
    - COMPLETED: Operation successfully finished and verified.
    - BLOCKED: Operation obstructed by an issue or missing resource.
    """
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class OperationExecutionTransitionRequest(BaseModel):
    """
    Request payload to transition an operation execution to a new state.
    Strictly forbids injection of timestamps, user_id, or duration.
    """
    model_config = ConfigDict(extra="forbid")

    target_status: ExecutionStatus = Field(
        ...,
        description="The target state to transition to: ready, in_progress, paused, completed, or blocked",
    )
    operator_notes: Optional[str] = Field(
        None,
        description="Optional artisan or workshop supervisor notes regarding the transition",
        max_length=2000,
    )
    worker_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional artisan/worker ID performing this operation",
    )
    machine_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional machine/equipment ID utilized for this operation",
    )
    validate_resources: Optional[bool] = Field(
        None,
        description="Optional override to strictly enforce or bypass required worker/machine checks on start",
    )


class WorkerAssignmentRequest(BaseModel):
    """Payload to assign an eligible artisan to an operation execution."""
    model_config = ConfigDict(extra="forbid")

    worker_id: uuid.UUID = Field(
        ...,
        description="ID of the eligible workshop artisan to assign",
    )


class MachineAssignmentRequest(BaseModel):
    """Payload to assign compatible equipment to an operation execution."""
    model_config = ConfigDict(extra="forbid")

    machine_id: uuid.UUID = Field(
        ...,
        description="ID of the compatible equipment to assign",
    )


class OperationExecutionCreate(BaseModel):
    """
    Payload for directly creating an operation execution record.
    Strictly forbids client-controlled user_id, timestamps, or durations.
    """
    model_config = ConfigDict(extra="forbid")

    production_order_id: uuid.UUID = Field(
        ...,
        description="ID of the production order being manufactured",
    )
    production_step_id: uuid.UUID = Field(
        ...,
        description="ID of the manufacturing routing step being executed",
    )
    scheduled_task_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional ID of the CP-SAT scheduled task planned for this operation",
    )
    worker_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional ID of the assigned artisan",
    )
    machine_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional ID of the assigned equipment",
    )
    operator_notes: Optional[str] = Field(
        None,
        description="Optional initial execution or setup notes",
        max_length=2000,
    )


class OperationExecutionResponse(BaseModel):
    """
    Authoritative response schema for an OperationExecution record.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    production_order_id: uuid.UUID
    production_step_id: uuid.UUID
    scheduled_task_id: Optional[uuid.UUID] = None
    worker_id: Optional[uuid.UUID] = None
    machine_id: Optional[uuid.UUID] = None

    status: ExecutionStatus

    # Planned timing (CP-SAT schedule or estimated)
    planned_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None
    planned_duration_hours: Optional[float] = None

    # Actual shop-floor timing
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    actual_duration_hours: Optional[float] = None
    pause_duration_hours: float = 0.0
    last_paused_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    operator_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Denormalized context fields for UI / inspection
    step_number: Optional[int] = None
    stage_name: Optional[str] = None
    required_skill: Optional[str] = None
    required_machine_type: Optional[str] = None
    quality_checkpoint: Optional[str] = None
    worker_name: Optional[str] = None
    machine_name: Optional[str] = None

    # Planned vs Actual resources (Phase J.3)
    actual_worker_id: Optional[uuid.UUID] = None
    actual_machine_id: Optional[uuid.UUID] = None
    planned_worker_id: Optional[uuid.UUID] = None
    planned_machine_id: Optional[uuid.UUID] = None
    planned_worker_name: Optional[str] = None
    planned_machine_name: Optional[str] = None

    # Resource validation & eligibility flags (Phase J.3)
    worker_skill: Optional[str] = None
    machine_type: Optional[str] = None
    worker_eligible: Optional[bool] = None
    machine_compatible: Optional[bool] = None

    # Workflow indicators (Phase J.2)
    is_terminal: bool = False
    can_start: bool = False
    has_uncompleted_predecessors: bool = False

    # Phase J.5 Controlled Rework & Quality Control
    execution_type: str = "normal"
    rework_of_execution_id: Optional[uuid.UUID] = None
    attempt_number: int = 1
    latest_qc_result: Optional[str] = None
    latest_defect_severity: Optional[str] = None
    quality_gate_passed: bool = False


class OperationExecutionListResponse(BaseModel):
    """
    List response containing all execution records for a production order
    with workflow progress metrics (Phase J.2).
    """
    model_config = ConfigDict(from_attributes=True)

    order_id: uuid.UUID
    total: int
    items: List[OperationExecutionResponse]

    # Workflow summary metrics
    order_status: Optional[str] = None
    completed_count: int = 0
    in_progress_count: int = 0
    ready_count: int = 0
    pending_count: int = 0
    blocked_count: int = 0
    current_step_number: Optional[int] = None
    overall_progress_percent: float = 0.0


# =========================================================================
# Phase J.4: Material Consumption & Wastage Tracking Schemas
# =========================================================================

class MaterialCategory(str, Enum):
    """Broad categories for jewellery manufacturing materials."""
    METAL = "METAL"
    GEMSTONE = "GEMSTONE"


class MaterialConsumptionCreate(BaseModel):
    """
    Payload for recording actual material consumption against an operation execution.
    Strictly forbids client-controlled user_id, production_order_id, operation_execution_id,
    or timestamps to enforce tenant security and historical integrity.
    """
    model_config = ConfigDict(extra="forbid")

    material_type: Optional[str] = Field(
        None,
        description="Material category: METAL or GEMSTONE. If omitted and spec item is linked, derived automatically.",
    )
    material_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Name of the material (e.g. '18K Yellow Gold', '0.50ct Round Diamond'). Auto-derived if spec item is linked.",
    )
    unit: Optional[str] = Field(
        "g",
        min_length=1,
        max_length=50,
        description="Unit of measurement (e.g., 'g', 'grams', 'cts', 'carats', 'pcs')",
    )
    planned_quantity: float = Field(
        default=0.0,
        ge=0.0,
        description="Planned quantity from specification baseline (non-negative)",
    )
    actual_quantity: float = Field(
        ...,
        ge=0.0,
        description="Actual quantity consumed on the bench (non-negative)",
    )
    wastage_quantity: float = Field(
        default=0.0,
        ge=0.0,
        description="Quantity lost as scrap, dust, casting loss, or damage (non-negative)",
    )
    wastage_reason: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional description or cause for wastage",
    )
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional shop-floor operator notes regarding this material draw",
    )
    specification_material_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional reference to the authoritative ProductionMaterial item in the specification",
    )
    specification_gemstone_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional reference to the authoritative ProductionGemstone item in the specification",
    )

    @model_validator(mode="after")
    def validate_quantities_and_types(self):
        if self.actual_quantity < 0.0:
            raise ValueError("actual_quantity must be non-negative.")
        if self.wastage_quantity < 0.0:
            raise ValueError("wastage_quantity must be non-negative.")
        if self.planned_quantity < 0.0:
            raise ValueError("planned_quantity must be non-negative.")
        if self.wastage_quantity > self.actual_quantity:
            raise ValueError("wastage_quantity cannot exceed actual_quantity.")

        if self.material_type is not None:
            normalized = self.material_type.strip().upper()
            if normalized not in ("METAL", "GEMSTONE"):
                raise ValueError(
                    f"Invalid material_type '{self.material_type}'. Must be 'METAL' or 'GEMSTONE'."
                )
            self.material_type = normalized

        # If no specification item is linked, material_name and material_type must be provided
        if not self.specification_material_id and not self.specification_gemstone_id:
            if not self.material_name or not self.material_name.strip():
                raise ValueError(
                    "material_name is required when not linking to a specification item."
                )
            if not self.material_type:
                raise ValueError(
                    "material_type is required ('METAL' or 'GEMSTONE') when not linking to a specification item."
                )
        return self


class MaterialConsumptionResponse(BaseModel):
    """
    Authoritative response schema for an actual MaterialConsumption record.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    production_order_id: uuid.UUID
    operation_execution_id: uuid.UUID
    specification_material_id: Optional[uuid.UUID] = None
    specification_gemstone_id: Optional[uuid.UUID] = None

    material_type: str
    material_name: str
    unit: str
    planned_quantity: float
    actual_quantity: float
    wastage_quantity: float
    wastage_reason: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class MaterialSummaryItem(BaseModel):
    """Summary item for planned vs actual material usage grouped by material."""
    model_config = ConfigDict(from_attributes=True)

    material_type: str
    material_name: str
    unit: str
    planned_quantity: float
    actual_quantity: float
    wastage_quantity: float
    net_consumed_quantity: float = 0.0


class OrderMaterialSummaryResponse(BaseModel):
    """Authoritative summary response for an order's planned vs actual material usage."""
    model_config = ConfigDict(from_attributes=True)

    order_id: uuid.UUID
    total_planned_quantity: float
    total_actual_quantity: float
    total_wastage_quantity: float
    total_net_quantity: float = 0.0
    items: List[MaterialSummaryItem]


# =========================================================================
# Phase J.5: Quality Control & Controlled Rework Schemas
# =========================================================================

class QualityCheckResult(str, Enum):
    """Authoritative quality control outcomes."""
    PASS = "PASS"
    FAIL = "FAIL"
    REWORK = "REWORK"


class DefectSeverity(str, Enum):
    """Graded defect severity levels for jewelry manufacturing quality checks."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class QualityCheckCreate(BaseModel):
    """
    Payload for recording a quality inspection against a completed operation execution.
    Strictly forbids client-controlled user_id, production_order_id, production_step_id,
    or checked_at timestamps.
    """
    model_config = ConfigDict(extra="forbid")

    result: QualityCheckResult = Field(
        ...,
        description="Quality check outcome: PASS, FAIL, or REWORK",
    )
    defect_severity: DefectSeverity = Field(
        default=DefectSeverity.NONE,
        description="Defect severity classification",
    )
    defect_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Defect code or category (e.g., 'POROSITY', 'PRONG_ALIGNMENT', 'SCRATCH')",
    )
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Inspector notes, audit observations, or rework guidance",
    )
    checked_by: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional inspector identity or badge number",
    )

    @model_validator(mode="after")
    def validate_result_and_severity(self):
        # Validate that FAIL or REWORK with NONE severity defaults or flags appropriately
        if self.result == QualityCheckResult.PASS and self.defect_severity not in (
            DefectSeverity.NONE,
            DefectSeverity.LOW,
        ):
            # In jewelry QA, a passing piece shouldn't have critical/high defect
            raise ValueError(
                f"A PASS result cannot have defect severity '{self.defect_severity.value}'."
            )
        return self


class QualityCheckResponse(BaseModel):
    """
    Authoritative response schema for a QualityCheck record.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    production_order_id: uuid.UUID
    operation_execution_id: uuid.UUID
    production_step_id: uuid.UUID

    result: str
    defect_severity: str
    defect_type: Optional[str] = None
    notes: Optional[str] = None
    checked_by: Optional[str] = None
    checked_at: datetime
    created_at: datetime
    updated_at: datetime

    # Contextual step / stage info
    step_number: Optional[int] = None
    stage_name: Optional[str] = None
    quality_checkpoint: Optional[str] = None


class ExecutionQualitySummaryItem(BaseModel):
    """Quality summary for a specific execution / attempt."""
    model_config = ConfigDict(from_attributes=True)

    execution_id: uuid.UUID
    step_id: uuid.UUID
    step_number: Optional[int] = None
    stage_name: Optional[str] = None
    execution_type: str = "normal"
    attempt_number: int = 1
    execution_status: str
    latest_qc_result: Optional[str] = None
    latest_defect_severity: Optional[str] = None
    total_checks: int = 0
    has_passed: bool = False


class OrderQualitySummaryResponse(BaseModel):
    """Authoritative summary response for an order's quality gate status."""
    model_config = ConfigDict(from_attributes=True)

    order_id: uuid.UUID
    total_operations: int
    completed_operations: int
    passed: int
    failed: int
    rework: int
    pending_quality_checks: int
    quality_gate_passed: bool
    items: List[ExecutionQualitySummaryItem]


class ReworkExecutionCreate(BaseModel):
    """Payload for explicitly authorizing and initializing a rework execution."""
    model_config = ConfigDict(extra="forbid")

    operator_notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Rework rationale, supervisor notes, or artisan instructions",
    )
