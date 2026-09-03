"""create production schedules and scheduled tasks tables

Revision ID: 0004_create_production_schedules_table
Revises: 0003_create_production_tables
Create Date: 2026-09-04 01:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004_create_production_schedules_table"
down_revision: Union[str, None] = "0003_create_production_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create production_schedules table
    op.create_table(
        "production_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False, server_default="Optimized Workshop Schedule"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("solver_status", sa.String(length=50), nullable=False, server_default="FEASIBLE"),
        sa.Column("makespan_hours", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_orders_scheduled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_orders_unscheduled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("worker_utilization_pct", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("machine_utilization_pct", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("runtime_seconds", sa.Float(), nullable=False, server_default="0.0"),
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
    op.create_index(op.f("ix_production_schedules_id"), "production_schedules", ["id"], unique=False)
    op.create_index(op.f("ix_production_schedules_user_id"), "production_schedules", ["user_id"], unique=False)
    op.create_index(op.f("ix_production_schedules_solver_status"), "production_schedules", ["solver_status"], unique=False)

    # 2. Create scheduled_tasks table
    op.create_table(
        "scheduled_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "schedule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_schedules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "machine_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("machines.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("operation_name", sa.String(length=255), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_hours", sa.Float(), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_overdue", sa.Boolean(), nullable=False, server_default="false"),
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
    op.create_index(op.f("ix_scheduled_tasks_id"), "scheduled_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_scheduled_tasks_schedule_id"), "scheduled_tasks", ["schedule_id"], unique=False)
    op.create_index(op.f("ix_scheduled_tasks_order_id"), "scheduled_tasks", ["order_id"], unique=False)
    op.create_index(op.f("ix_scheduled_tasks_worker_id"), "scheduled_tasks", ["worker_id"], unique=False)
    op.create_index(op.f("ix_scheduled_tasks_machine_id"), "scheduled_tasks", ["machine_id"], unique=False)
    op.create_index(op.f("ix_scheduled_tasks_start_time"), "scheduled_tasks", ["start_time"], unique=False)
    op.create_index(op.f("ix_scheduled_tasks_end_time"), "scheduled_tasks", ["end_time"], unique=False)


def downgrade() -> None:
    # Drop scheduled_tasks
    op.drop_index(op.f("ix_scheduled_tasks_end_time"), table_name="scheduled_tasks")
    op.drop_index(op.f("ix_scheduled_tasks_start_time"), table_name="scheduled_tasks")
    op.drop_index(op.f("ix_scheduled_tasks_machine_id"), table_name="scheduled_tasks")
    op.drop_index(op.f("ix_scheduled_tasks_worker_id"), table_name="scheduled_tasks")
    op.drop_index(op.f("ix_scheduled_tasks_order_id"), table_name="scheduled_tasks")
    op.drop_index(op.f("ix_scheduled_tasks_schedule_id"), table_name="scheduled_tasks")
    op.drop_index(op.f("ix_scheduled_tasks_id"), table_name="scheduled_tasks")
    op.drop_table("scheduled_tasks")

    # Drop production_schedules
    op.drop_index(op.f("ix_production_schedules_solver_status"), table_name="production_schedules")
    op.drop_index(op.f("ix_production_schedules_user_id"), table_name="production_schedules")
    op.drop_index(op.f("ix_production_schedules_id"), table_name="production_schedules")
    op.drop_table("production_schedules")
