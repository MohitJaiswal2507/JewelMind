"""create production tables (production_orders, workers, machines)

Revision ID: 0003_create_production_tables
Revises: 0002_create_designs
Create Date: 2026-09-04 01:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_create_production_tables"
down_revision: Union[str, None] = "0002_create_designs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create workers table
    op.create_table(
        "workers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("skill", sa.String(length=100), nullable=False, server_default="general"),
        sa.Column("capacity_hours_per_day", sa.Float(), nullable=False, server_default="8.0"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_workers_id"), "workers", ["id"], unique=False)
    op.create_index(op.f("ix_workers_user_id"), "workers", ["user_id"], unique=False)
    op.create_index(op.f("ix_workers_name"), "workers", ["name"], unique=False)
    op.create_index(op.f("ix_workers_skill"), "workers", ["skill"], unique=False)
    op.create_index(op.f("ix_workers_is_available"), "workers", ["is_available"], unique=False)

    # 2. Create machines table
    op.create_table(
        "machines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("machine_type", sa.String(length=100), nullable=False, server_default="general"),
        sa.Column("capacity_hours_per_day", sa.Float(), nullable=False, server_default="8.0"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_machines_id"), "machines", ["id"], unique=False)
    op.create_index(op.f("ix_machines_user_id"), "machines", ["user_id"], unique=False)
    op.create_index(op.f("ix_machines_name"), "machines", ["name"], unique=False)
    op.create_index(op.f("ix_machines_machine_type"), "machines", ["machine_type"], unique=False)
    op.create_index(op.f("ix_machines_is_available"), "machines", ["is_available"], unique=False)

    # 3. Create production_orders table
    op.create_table(
        "production_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "design_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("designs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("priority", sa.String(length=50), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_production_orders_id"), "production_orders", ["id"], unique=False)
    op.create_index(op.f("ix_production_orders_user_id"), "production_orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_production_orders_design_id"), "production_orders", ["design_id"], unique=False)
    op.create_index(op.f("ix_production_orders_priority"), "production_orders", ["priority"], unique=False)
    op.create_index(op.f("ix_production_orders_status"), "production_orders", ["status"], unique=False)
    op.create_index(op.f("ix_production_orders_deadline"), "production_orders", ["deadline"], unique=False)


def downgrade() -> None:
    # Drop production_orders
    op.drop_index(op.f("ix_production_orders_deadline"), table_name="production_orders")
    op.drop_index(op.f("ix_production_orders_status"), table_name="production_orders")
    op.drop_index(op.f("ix_production_orders_priority"), table_name="production_orders")
    op.drop_index(op.f("ix_production_orders_design_id"), table_name="production_orders")
    op.drop_index(op.f("ix_production_orders_user_id"), table_name="production_orders")
    op.drop_index(op.f("ix_production_orders_id"), table_name="production_orders")
    op.drop_table("production_orders")

    # Drop machines
    op.drop_index(op.f("ix_machines_is_available"), table_name="machines")
    op.drop_index(op.f("ix_machines_machine_type"), table_name="machines")
    op.drop_index(op.f("ix_machines_name"), table_name="machines")
    op.drop_index(op.f("ix_machines_user_id"), table_name="machines")
    op.drop_index(op.f("ix_machines_id"), table_name="machines")
    op.drop_table("machines")

    # Drop workers
    op.drop_index(op.f("ix_workers_is_available"), table_name="workers")
    op.drop_index(op.f("ix_workers_skill"), table_name="workers")
    op.drop_index(op.f("ix_workers_name"), table_name="workers")
    op.drop_index(op.f("ix_workers_user_id"), table_name="workers")
    op.drop_index(op.f("ix_workers_id"), table_name="workers")
    op.drop_table("workers")
