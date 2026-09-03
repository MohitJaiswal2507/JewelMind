import uuid
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.design import Design
    from app.models.production import ProductionOrder, Worker, Machine


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User entity representing registered system users and jewellery artisans.
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="user",
        nullable=False,
    )

    # Relationships
    designs: Mapped[List["Design"]] = relationship(
        "Design",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    production_orders: Mapped[List["ProductionOrder"]] = relationship(
        "ProductionOrder",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    workers: Mapped[List["Worker"]] = relationship(
        "Worker",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    machines: Mapped[List["Machine"]] = relationship(
        "Machine",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"
