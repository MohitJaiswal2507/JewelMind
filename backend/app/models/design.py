"""
Design SQLAlchemy ORM Model
"""

import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.production import ProductionOrder
    from app.models.specification import ProductionSpecification


class Design(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Design entity representing a jewellery design created and owned by a user.
    """
    __tablename__ = "designs"

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
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
        index=True,
    )
    sketch_image_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    rendered_image_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    ai_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="designs")
    production_orders: Mapped[list["ProductionOrder"]] = relationship(
        "ProductionOrder",
        back_populates="design",
        cascade="all, delete-orphan",
    )
    renders: Mapped[list["DesignRender"]] = relationship(
        "DesignRender",
        back_populates="design",
        cascade="all, delete-orphan",
        order_by="DesignRender.version_number",
    )
    specifications: Mapped[list["ProductionSpecification"]] = relationship(
        "ProductionSpecification",
        back_populates="design",
        cascade="all, delete-orphan",
        order_by="ProductionSpecification.version_number",
    )

    def __repr__(self) -> str:
        return f"<Design id={self.id} name='{self.name}' category='{self.category}' status='{self.status}'>"


class DesignRender(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    DesignRender entity representing a persistent, versioned photorealistic synthesis
    for a specific jewellery design.
    """
    __tablename__ = "design_renders"

    design_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("designs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        index=True,
    )
    parent_render_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("design_renders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    render_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="text",
        index=True,
    )
    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    enhanced_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    structured_state: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    image_url: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    control_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="none",
    )
    control_strength: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    seed: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    is_approved_for_production: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # Relationships
    design: Mapped["Design"] = relationship("Design", back_populates="renders")
    user: Mapped["User"] = relationship("User")
    parent_render: Mapped[Optional["DesignRender"]] = relationship(
        "DesignRender",
        remote_side="DesignRender.id",
        foreign_keys=[parent_render_id],
    )
    specifications: Mapped[list["ProductionSpecification"]] = relationship(
        "ProductionSpecification",
        back_populates="render",
    )

    def __repr__(self) -> str:
        return (
            f"<DesignRender id={self.id} design_id={self.design_id} "
            f"v={self.version_number} mode='{self.render_mode}' approved={self.is_approved_for_production}>"
        )

