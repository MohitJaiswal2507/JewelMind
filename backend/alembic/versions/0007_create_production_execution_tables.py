"""create operation_executions table for shop-floor production tracking

Revision ID: 0007_create_production_execution_tables
Revises: 0006_create_production_specifications
Create Date: 2026-09-25 12:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007_create_production_execution_tables"
down_revision: Union[str, None] = "0006_create_production_specifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create operation_executions table
    op.create_table(
        "operation_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "production_order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "production_step_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_steps.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "scheduled_task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scheduled_tasks.id", ondelete="SET NULL"),
            nullable=True,
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
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("planned_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_duration_hours", sa.Float(), nullable=True),
        sa.Column("actual_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_duration_hours", sa.Float(), nullable=True),
        sa.Column(
            "pause_duration_hours",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column("last_paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("operator_notes", sa.Text(), nullable=True),
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
            nullable=False,
        ),
        sa.UniqueConstraint(
            "production_order_id",
            "production_step_id",
            name="uq_operation_executions_order_step",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'ready', 'in_progress', 'paused', 'completed', 'blocked')",
            name="ck_operation_executions_status",
        ),
        sa.CheckConstraint(
            "pause_duration_hours >= 0.0",
            name="ck_operation_executions_pause_duration",
        ),
        sa.CheckConstraint(
            "actual_duration_hours IS NULL OR actual_duration_hours >= 0.0",
            name="ck_operation_executions_actual_duration",
        ),
        sa.CheckConstraint(
            "planned_duration_hours IS NULL OR planned_duration_hours >= 0.0",
            name="ck_operation_executions_planned_duration",
        ),
    )

    # 2. Create indexes
    op.create_index("ix_operation_executions_user_id", "operation_executions", ["user_id"])
    op.create_index("ix_operation_executions_order_id", "operation_executions", ["production_order_id"])
    op.create_index("ix_operation_executions_step_id", "operation_executions", ["production_step_id"])
    op.create_index("ix_operation_executions_task_id", "operation_executions", ["scheduled_task_id"])
    op.create_index("ix_operation_executions_worker_id", "operation_executions", ["worker_id"])
    op.create_index("ix_operation_executions_machine_id", "operation_executions", ["machine_id"])
    op.create_index("ix_operation_executions_status", "operation_executions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_operation_executions_status", table_name="operation_executions")
    op.drop_index("ix_operation_executions_machine_id", table_name="operation_executions")
    op.drop_index("ix_operation_executions_worker_id", table_name="operation_executions")
    op.drop_index("ix_operation_executions_task_id", table_name="operation_executions")
    op.drop_index("ix_operation_executions_step_id", table_name="operation_executions")
    op.drop_index("ix_operation_executions_order_id", table_name="operation_executions")
    op.drop_index("ix_operation_executions_user_id", table_name="operation_executions")
    op.drop_table("operation_executions")
