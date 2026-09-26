"""
Pydantic Schemas for Production Execution (Shop-Floor Operation Tracking)
Enforces strict client input validation, forbidding client-controlled timestamps
or tenant/audit fields, while providing structured execution state contracts.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


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


class OperationExecutionListResponse(BaseModel):
    """
    List response containing all execution records for a production order.
    """
    model_config = ConfigDict(from_attributes=True)

    order_id: uuid.UUID
    total: int
    items: List[OperationExecutionResponse]
