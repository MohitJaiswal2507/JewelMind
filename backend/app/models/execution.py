"""
Production Execution SQLAlchemy ORM Models
Defines OperationExecution representing actual workshop floor execution
of manufacturing routing steps for a production order.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.production import Machine, ProductionOrder, Worker
    from app.models.schedule import ScheduledTask
    from app.models.specification import (
        ProductionGemstone,
        ProductionMaterial,
        ProductionStep,
    )
    from app.models.user import User


class OperationExecution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    OperationExecution entity representing the actual shop-floor execution
    of a specific manufacturing routing step (ProductionStep) belonging to a ProductionOrder.
    
    Architectural distinction:
    - ProductionStep: defines WHAT should be done (manufacturing engineering).
    - ScheduledTask: defines WHEN and by WHOM it was PLANNED (CP-SAT solver).
    - OperationExecution: defines WHAT ACTUALLY HAPPENED on the workshop bench.
    """
    __tablename__ = "operation_executions"
    __table_args__ = (
        UniqueConstraint(
            "production_order_id",
            "production_step_id",
            name="uq_operation_executions_order_step",
        ),
        CheckConstraint(
            "status IN ('pending', 'ready', 'in_progress', 'paused', 'completed', 'blocked')",
            name="ck_operation_executions_status",
        ),
        CheckConstraint(
            "pause_duration_hours >= 0.0",
            name="ck_operation_executions_pause_duration",
        ),
        CheckConstraint(
            "actual_duration_hours IS NULL OR actual_duration_hours >= 0.0",
            name="ck_operation_executions_actual_duration",
        ),
        CheckConstraint(
            "planned_duration_hours IS NULL OR planned_duration_hours >= 0.0",
            name="ck_operation_executions_planned_duration",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # RESTRICT preserves actual manufacturing history; prevents deleting orders that have started execution
    production_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # RESTRICT prevents deleting steps while execution history references them
    production_step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_steps.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Optional link to CP-SAT schedule allocation
    scheduled_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheduled_tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Assigned artisan executing the step
    worker_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Assigned equipment used during execution
    machine_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("machines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # State: pending -> ready -> in_progress -> paused -> completed (or blocked)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    # Planned timing (copied from ScheduledTask or calculated if schedule exists)
    planned_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    planned_end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    planned_duration_hours: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Actual shop-floor execution timing
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    actual_end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    actual_duration_hours: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    pause_duration_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    last_paused_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Shop-floor operator log and handoff notes
    operator_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    production_order: Mapped["ProductionOrder"] = relationship(
        "ProductionOrder",
        back_populates="executions",
    )
    production_step: Mapped["ProductionStep"] = relationship("ProductionStep")
    scheduled_task: Mapped[Optional["ScheduledTask"]] = relationship("ScheduledTask")
    worker: Mapped[Optional["Worker"]] = relationship("Worker")
    machine: Mapped[Optional["Machine"]] = relationship("Machine")
    material_consumptions: Mapped[List["MaterialConsumption"]] = relationship(
        "MaterialConsumption",
        back_populates="operation_execution",
        cascade="all, delete-orphan",
        order_by="MaterialConsumption.created_at",
    )

    def __repr__(self) -> str:
        return (
            f"<OperationExecution id={self.id} order_id={self.production_order_id} "
            f"step_id={self.production_step_id} status='{self.status}'>"
        )


class MaterialConsumption(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    MaterialConsumption entity representing actual shop-floor material usage and wastage
    recorded during the execution of a specific manufacturing routing step (OperationExecution)
    for a ProductionOrder.

    Traceability chain:
    ProductionSpecification -> ProductionOrder -> OperationExecution -> MaterialConsumption
    """
    __tablename__ = "material_consumptions"
    __table_args__ = (
        CheckConstraint(
            "actual_quantity >= 0.0",
            name="ck_material_consumptions_actual_quantity",
        ),
        CheckConstraint(
            "wastage_quantity >= 0.0",
            name="ck_material_consumptions_wastage_quantity",
        ),
        CheckConstraint(
            "planned_quantity >= 0.0",
            name="ck_material_consumptions_planned_quantity",
        ),
        CheckConstraint(
            "wastage_quantity <= actual_quantity",
            name="ck_material_consumptions_wastage_lte_actual",
        ),
        CheckConstraint(
            "material_type IN ('metal', 'gemstone', 'METAL', 'GEMSTONE')",
            name="ck_material_consumptions_material_type",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    production_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    operation_execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("operation_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    specification_material_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_materials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    specification_gemstone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_gemstones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    material_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    material_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="g",
    )
    planned_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    actual_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    wastage_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    wastage_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    production_order: Mapped["ProductionOrder"] = relationship(
        "ProductionOrder",
        back_populates="material_consumptions",
    )
    operation_execution: Mapped["OperationExecution"] = relationship(
        "OperationExecution",
        back_populates="material_consumptions",
    )
    specification_material: Mapped[Optional["ProductionMaterial"]] = relationship(
        "ProductionMaterial",
    )
    specification_gemstone: Mapped[Optional["ProductionGemstone"]] = relationship(
        "ProductionGemstone",
    )

    def __repr__(self) -> str:
        return (
            f"<MaterialConsumption id={self.id} order_id={self.production_order_id} "
            f"execution_id={self.operation_execution_id} type='{self.material_type}' "
            f"actual={self.actual_quantity} wastage={self.wastage_quantity}>"
        )
