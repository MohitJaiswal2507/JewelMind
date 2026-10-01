"""
Production Management SQLAlchemy ORM Models
Includes ProductionOrder, Worker, and Machine entities for workshop operations.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.design import Design
    from app.models.execution import MaterialConsumption, OperationExecution, QualityCheck
    from app.models.specification import ProductionSpecification
    from app.models.user import User


class ProductionOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    ProductionOrder entity representing a scheduled jewellery manufacturing batch
    linked to a specific customer/artisan Design.
    """
    __tablename__ = "production_orders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    design_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("designs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="medium",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )
    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    render_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("design_renders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approved_render_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    specification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_specifications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="production_orders")
    design: Mapped["Design"] = relationship("Design", back_populates="production_orders")
    specification: Mapped[Optional["ProductionSpecification"]] = relationship(
        "ProductionSpecification",
        back_populates="production_orders",
    )
    executions: Mapped[list["OperationExecution"]] = relationship(
        "OperationExecution",
        back_populates="production_order",
        order_by="OperationExecution.created_at",
    )
    material_consumptions: Mapped[list["MaterialConsumption"]] = relationship(
        "MaterialConsumption",
        back_populates="production_order",
        order_by="MaterialConsumption.created_at",
    )
    quality_checks: Mapped[list["QualityCheck"]] = relationship(
        "QualityCheck",
        back_populates="production_order",
        order_by="QualityCheck.checked_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<ProductionOrder id={self.id} design_id={self.design_id} qty={self.quantity} priority='{self.priority}' status='{self.status}'>"



class Worker(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Worker entity representing a workshop artisan with a primary craft skill
    and daily productive capacity (hours/day).
    """
    __tablename__ = "workers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    skill: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="general",
        index=True,
    )
    capacity_hours_per_day: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=8.0,
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="workers")

    def __repr__(self) -> str:
        return f"<Worker id={self.id} name='{self.name}' skill='{self.skill}' cap={self.capacity_hours_per_day}h avail={self.is_available}>"


class Machine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Machine entity representing specialized jewellery manufacturing equipment
    with daily operational capacity (hours/day).
    """
    __tablename__ = "machines"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    machine_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="general",
        index=True,
    )
    capacity_hours_per_day: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=8.0,
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="machines")

    def __repr__(self) -> str:
        return f"<Machine id={self.id} name='{self.name}' type='{self.machine_type}' cap={self.capacity_hours_per_day}h avail={self.is_available}>"
