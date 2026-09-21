"""
Production Specification SQLAlchemy ORM Models
Defines ProductionSpecification, ProductionMaterial, ProductionGemstone, and ProductionStep.
Enforces render-locked immutability, multi-tenant isolation, and cascade cleanup of child BOM items.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.design import Design, DesignRender
    from app.models.production import ProductionOrder
    from app.models.user import User


class ProductionSpecification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    ProductionSpecification entity representing an authoritative manufacturing blueprint (BOM & routing)
    permanently bound to an approved DesignRender version.
    """
    __tablename__ = "production_specifications"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "design_id",
            "version_number",
            name="uq_production_specifications_user_design_version",
        ),
        CheckConstraint("version_number > 0", name="ck_production_specifications_version_number"),
        CheckConstraint("total_gemstone_count >= 0", name="ck_production_specifications_gemstone_count"),
        CheckConstraint(
            "ai_confidence_score IS NULL OR (ai_confidence_score >= 0.0 AND ai_confidence_score <= 1.0)",
            name="ck_production_specifications_ai_confidence",
        ),
        CheckConstraint(
            "status IN ('draft', 'approved', 'archived')",
            name="ck_production_specifications_status",
        ),
        CheckConstraint(
            "complexity_rating IS NULL OR complexity_rating IN ('simple', 'moderate', 'intricate', 'masterpiece')",
            name="ck_production_specifications_complexity",
        ),
    )

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
    # RESTRICT prevents deletion of an approved render referenced by an active specification
    render_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("design_renders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Estimated metrics (AI inference or artisan preliminary estimates)
    estimated_rough_metal_weight_grams: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    estimated_finished_metal_weight_grams: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    total_gemstone_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    estimated_total_bench_hours: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    complexity_rating: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Additional notes and audit fields
    fabrication_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="specifications")
    design: Mapped["Design"] = relationship("Design", back_populates="specifications")
    render: Mapped["DesignRender"] = relationship("DesignRender", back_populates="specifications")

    materials: Mapped[List["ProductionMaterial"]] = relationship(
        "ProductionMaterial",
        back_populates="specification",
        cascade="all, delete-orphan",
        order_by="ProductionMaterial.created_at",
    )
    gemstones: Mapped[List["ProductionGemstone"]] = relationship(
        "ProductionGemstone",
        back_populates="specification",
        cascade="all, delete-orphan",
        order_by="ProductionGemstone.created_at",
    )
    steps: Mapped[List["ProductionStep"]] = relationship(
        "ProductionStep",
        back_populates="specification",
        cascade="all, delete-orphan",
        order_by="ProductionStep.step_number",
    )
    production_orders: Mapped[List["ProductionOrder"]] = relationship(
        "ProductionOrder",
        back_populates="specification",
    )

    def __repr__(self) -> str:
        return (
            f"<ProductionSpecification id={self.id} design_id={self.design_id} "
            f"render_id={self.render_id} v={self.version_number} status='{self.status}'>"
        )


class ProductionMaterial(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    ProductionMaterial entity representing metal alloy requirements and finishing specifications
    within a ProductionSpecification BOM.
    """
    __tablename__ = "production_materials"
    __table_args__ = (
        CheckConstraint(
            "estimated_weight_grams IS NULL OR estimated_weight_grams >= 0.0",
            name="ck_production_materials_weight",
        ),
        CheckConstraint(
            "casting_loss_percentage IS NULL OR casting_loss_percentage >= 0.0",
            name="ck_production_materials_loss",
        ),
    )

    specification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metal_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    metal_purity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    metal_color: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    metal_finish: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    plating: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    estimated_weight_grams: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    casting_loss_percentage: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=10.0,
    )

    # Relationships
    specification: Mapped["ProductionSpecification"] = relationship(
        "ProductionSpecification",
        back_populates="materials",
    )

    def __repr__(self) -> str:
        return (
            f"<ProductionMaterial id={self.id} spec_id={self.specification_id} "
            f"metal='{self.metal_type} {self.metal_purity}' weight={self.estimated_weight_grams}g>"
        )


class ProductionGemstone(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    ProductionGemstone entity representing gemstone line items in a ProductionSpecification BOM.
    """
    __tablename__ = "production_gemstones"
    __table_args__ = (
        CheckConstraint("stone_count >= 0", name="ck_production_gemstones_count"),
        CheckConstraint(
            "estimated_carat_weight IS NULL OR estimated_carat_weight >= 0.0",
            name="ck_production_gemstones_carat",
        ),
    )

    specification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gemstone_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    cut_shape: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    stone_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    estimated_carat_weight: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    approximate_dimensions_mm: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    setting_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    is_center_stone: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Relationships
    specification: Mapped["ProductionSpecification"] = relationship(
        "ProductionSpecification",
        back_populates="gemstones",
    )

    def __repr__(self) -> str:
        return (
            f"<ProductionGemstone id={self.id} spec_id={self.specification_id} "
            f"type='{self.gemstone_type}' count={self.stone_count} center={self.is_center_stone}>"
        )


class ProductionStep(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    ProductionStep entity representing sequential workshop routing stages in a ProductionSpecification.
    """
    __tablename__ = "production_steps"
    __table_args__ = (
        UniqueConstraint(
            "specification_id",
            "step_number",
            name="uq_production_steps_spec_step_number",
        ),
        CheckConstraint("step_number > 0", name="ck_production_steps_step_number"),
        CheckConstraint("base_hours >= 0.0", name="ck_production_steps_base_hours"),
        CheckConstraint("per_unit_hours >= 0.0", name="ck_production_steps_per_unit_hours"),
    )

    specification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    stage_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    required_skill: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    required_machine_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    base_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    per_unit_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    quality_checkpoint: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    specification: Mapped["ProductionSpecification"] = relationship(
        "ProductionSpecification",
        back_populates="steps",
    )

    def __repr__(self) -> str:
        return (
            f"<ProductionStep id={self.id} spec_id={self.specification_id} "
            f"#{self.step_number} '{self.stage_name}' skill='{self.required_skill}'>"
        )
