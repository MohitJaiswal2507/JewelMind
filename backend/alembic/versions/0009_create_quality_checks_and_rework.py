"""create quality_checks table and add rework fields to operation_executions

Revision ID: 0009_create_quality_checks_and_rework
Revises: 0008_create_material_consumption_table
Create Date: 2026-10-01 20:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0009_create_quality_checks_and_rework"
down_revision: Union[str, None] = "0008_create_material_consumption_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add rework columns to operation_executions
    op.add_column(
        "operation_executions",
        sa.Column("execution_type", sa.String(length=50), nullable=False, server_default="normal"),
    )
    op.add_column(
        "operation_executions",
        sa.Column(
            "rework_of_execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("operation_executions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "operation_executions",
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index(
        "ix_operation_executions_rework_of_id",
        "operation_executions",
        ["rework_of_execution_id"],
    )

    # 2. Update unique constraint on operation_executions to allow multiple attempts (reworks)
    op.drop_constraint("uq_operation_executions_order_step", "operation_executions", type_="unique")
    op.create_unique_constraint(
        "uq_operation_executions_order_step_attempt",
        "operation_executions",
        ["production_order_id", "production_step_id", "attempt_number"],
    )

    # 3. Create quality_checks table
    op.create_table(
        "quality_checks",
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
            "operation_execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("operation_executions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "production_step_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_steps.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("result", sa.String(length=50), nullable=False),
        sa.Column("defect_severity", sa.String(length=50), nullable=False, server_default="NONE"),
        sa.Column("defect_type", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("checked_by", sa.String(length=100), nullable=True),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
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
        sa.CheckConstraint(
            "result IN ('PASS', 'FAIL', 'REWORK', 'pass', 'fail', 'rework')",
            name="ck_quality_checks_result",
        ),
        sa.CheckConstraint(
            "defect_severity IN ('NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'none', 'low', 'medium', 'high', 'critical')",
            name="ck_quality_checks_defect_severity",
        ),
    )

    # 4. Create indexes on quality_checks
    op.create_index("ix_quality_checks_user_id", "quality_checks", ["user_id"])
    op.create_index("ix_quality_checks_production_order_id", "quality_checks", ["production_order_id"])
    op.create_index("ix_quality_checks_operation_execution_id", "quality_checks", ["operation_execution_id"])
    op.create_index("ix_quality_checks_production_step_id", "quality_checks", ["production_step_id"])
    op.create_index("ix_quality_checks_result", "quality_checks", ["result"])
    op.create_index("ix_quality_checks_checked_at", "quality_checks", ["checked_at"])


def downgrade() -> None:
    # 1. Drop quality_checks indexes and table
    op.drop_index("ix_quality_checks_checked_at", table_name="quality_checks")
    op.drop_index("ix_quality_checks_result", table_name="quality_checks")
    op.drop_index("ix_quality_checks_production_step_id", table_name="quality_checks")
    op.drop_index("ix_quality_checks_operation_execution_id", table_name="quality_checks")
    op.drop_index("ix_quality_checks_production_order_id", table_name="quality_checks")
    op.drop_index("ix_quality_checks_user_id", table_name="quality_checks")
    op.drop_table("quality_checks")

    # 2. Revert unique constraint on operation_executions
    op.drop_constraint("uq_operation_executions_order_step_attempt", "operation_executions", type_="unique")
    op.create_unique_constraint(
        "uq_operation_executions_order_step",
        "operation_executions",
        ["production_order_id", "production_step_id"],
    )

    # 3. Drop rework columns from operation_executions
    op.drop_index("ix_operation_executions_rework_of_id", table_name="operation_executions")
    op.drop_column("operation_executions", "attempt_number")
    op.drop_column("operation_executions", "rework_of_execution_id")
    op.drop_column("operation_executions", "execution_type")
