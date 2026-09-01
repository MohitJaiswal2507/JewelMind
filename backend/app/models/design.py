"""
Design SQLAlchemy ORM Model
"""

import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


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

    # Relationship to user
    user: Mapped["User"] = relationship("User", back_populates="designs")

    def __repr__(self) -> str:
        return f"<Design id={self.id} name='{self.name}' category='{self.category}' status='{self.status}'>"
