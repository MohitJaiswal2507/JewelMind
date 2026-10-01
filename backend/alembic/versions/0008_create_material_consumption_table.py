"""create material_consumptions table for shop-floor material usage and wastage tracking

Revision ID: 0008_create_material_consumption_table
Revises: 0007_create_production_execution_tables
Create Date: 2026-10-01 19:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0008_create_material_consumption_table"
down_revision: Union[str, None] = "0007_create_production_execution_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create material_consumptions table
    op.create_table(
        "material_consumptions",
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
            "specification_material_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_materials.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "specification_gemstone_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_gemstones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("material_type", sa.String(length=50), nullable=False),
        sa.Column("material_name", sa.String(length=100), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False, server_default="g"),
        sa.Column("planned_quantity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("actual_quantity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("wastage_quantity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("wastage_reason", sa.String(length=255), nullable=True),
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
            nullable=False,
        ),
        sa.CheckConstraint(
            "actual_quantity >= 0.0",
            name="ck_material_consumptions_actual_quantity",
        ),
        sa.CheckConstraint(
            "wastage_quantity >= 0.0",
            name="ck_material_consumptions_wastage_quantity",
        ),
        sa.CheckConstraint(
            "planned_quantity >= 0.0",
            name="ck_material_consumptions_planned_quantity",
        ),
        sa.CheckConstraint(
            "wastage_quantity <= actual_quantity",
            name="ck_material_consumptions_wastage_lte_actual",
        ),
        sa.CheckConstraint(
            "material_type IN ('metal', 'gemstone', 'METAL', 'GEMSTONE')",
            name="ck_material_consumptions_material_type",
        ),
    )

    # 2. Create indexes
    op.create_index("ix_material_consumptions_user_id", "material_consumptions", ["user_id"])
    op.create_index("ix_material_consumptions_order_id", "material_consumptions", ["production_order_id"])
    op.create_index("ix_material_consumptions_execution_id", "material_consumptions", ["operation_execution_id"])
    op.create_index("ix_material_consumptions_spec_material_id", "material_consumptions", ["specification_material_id"])
    op.create_index("ix_material_consumptions_spec_gemstone_id", "material_consumptions", ["specification_gemstone_id"])
    op.create_index("ix_material_consumptions_material_type", "material_consumptions", ["material_type"])


def downgrade() -> None:
    op.drop_index("ix_material_consumptions_material_type", table_name="material_consumptions")
    op.drop_index("ix_material_consumptions_spec_gemstone_id", table_name="material_consumptions")
    op.drop_index("ix_material_consumptions_spec_material_id", table_name="material_consumptions")
    op.drop_index("ix_material_consumptions_execution_id", table_name="material_consumptions")
    op.drop_index("ix_material_consumptions_order_id", table_name="material_consumptions")
    op.drop_index("ix_material_consumptions_user_id", table_name="material_consumptions")
    op.drop_table("material_consumptions")
