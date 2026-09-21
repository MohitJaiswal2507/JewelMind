"""create production specifications and related BOM and step tables

Revision ID: 0006_create_production_specifications
Revises: 0005_create_design_renders_table
Create Date: 2026-09-22 00:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006_create_production_specifications"
down_revision: Union[str, None] = "0005_create_design_renders_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create production_specifications table
    op.create_table(
        "production_specifications",
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
        sa.Column(
            "render_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("design_renders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("estimated_rough_metal_weight_grams", sa.Float(), nullable=True),
        sa.Column("estimated_finished_metal_weight_grams", sa.Float(), nullable=True),
        sa.Column("total_gemstone_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_total_bench_hours", sa.Float(), nullable=True),
        sa.Column("complexity_rating", sa.String(length=50), nullable=True),
        sa.Column("fabrication_notes", sa.Text(), nullable=True),
        sa.Column("ai_confidence_score", sa.Float(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
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
            "user_id",
            "design_id",
            "version_number",
            name="uq_production_specifications_user_design_version",
        ),
        sa.CheckConstraint(
            "version_number > 0",
            name="ck_production_specifications_version_number",
        ),
        sa.CheckConstraint(
            "total_gemstone_count >= 0",
            name="ck_production_specifications_gemstone_count",
        ),
        sa.CheckConstraint(
            "ai_confidence_score IS NULL OR (ai_confidence_score >= 0.0 AND ai_confidence_score <= 1.0)",
            name="ck_production_specifications_ai_confidence",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'archived')",
            name="ck_production_specifications_status",
        ),
        sa.CheckConstraint(
            "complexity_rating IS NULL OR complexity_rating IN ('simple', 'moderate', 'intricate', 'masterpiece')",
            name="ck_production_specifications_complexity",
        ),
    )

    # Indexes on production_specifications
    op.create_index("ix_production_specifications_user_id", "production_specifications", ["user_id"])
    op.create_index("ix_production_specifications_design_id", "production_specifications", ["design_id"])
    op.create_index("ix_production_specifications_render_id", "production_specifications", ["render_id"])
    op.create_index("ix_production_specifications_status", "production_specifications", ["status"])
    op.create_index(
        "ix_production_specifications_design_version",
        "production_specifications",
        ["design_id", "version_number"],
    )

    # 2. Create production_materials table
    op.create_table(
        "production_materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "specification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_specifications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metal_type", sa.String(length=100), nullable=False),
        sa.Column("metal_purity", sa.String(length=50), nullable=False),
        sa.Column("metal_color", sa.String(length=50), nullable=True),
        sa.Column("metal_finish", sa.String(length=50), nullable=True),
        sa.Column("plating", sa.String(length=50), nullable=True),
        sa.Column("estimated_weight_grams", sa.Float(), nullable=True),
        sa.Column("casting_loss_percentage", sa.Float(), nullable=True, server_default="10.0"),
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
            "estimated_weight_grams IS NULL OR estimated_weight_grams >= 0.0",
            name="ck_production_materials_weight",
        ),
        sa.CheckConstraint(
            "casting_loss_percentage IS NULL OR casting_loss_percentage >= 0.0",
            name="ck_production_materials_loss",
        ),
    )
    op.create_index("ix_production_materials_specification_id", "production_materials", ["specification_id"])

    # 3. Create production_gemstones table
    op.create_table(
        "production_gemstones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "specification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_specifications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("gemstone_type", sa.String(length=100), nullable=False),
        sa.Column("cut_shape", sa.String(length=50), nullable=True),
        sa.Column("stone_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("estimated_carat_weight", sa.Float(), nullable=True),
        sa.Column("approximate_dimensions_mm", sa.String(length=100), nullable=True),
        sa.Column("setting_type", sa.String(length=50), nullable=True),
        sa.Column("is_center_stone", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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
        sa.CheckConstraint("stone_count >= 0", name="ck_production_gemstones_count"),
        sa.CheckConstraint(
            "estimated_carat_weight IS NULL OR estimated_carat_weight >= 0.0",
            name="ck_production_gemstones_carat",
        ),
    )
    op.create_index("ix_production_gemstones_specification_id", "production_gemstones", ["specification_id"])

    # 4. Create production_steps table
    op.create_table(
        "production_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "specification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_specifications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("stage_name", sa.String(length=255), nullable=False),
        sa.Column("required_skill", sa.String(length=100), nullable=False),
        sa.Column("required_machine_type", sa.String(length=100), nullable=True),
        sa.Column("base_hours", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("per_unit_hours", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quality_checkpoint", sa.String(length=500), nullable=True),
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
            "specification_id",
            "step_number",
            name="uq_production_steps_spec_step_number",
        ),
        sa.CheckConstraint("step_number > 0", name="ck_production_steps_step_number"),
        sa.CheckConstraint("base_hours >= 0.0", name="ck_production_steps_base_hours"),
        sa.CheckConstraint("per_unit_hours >= 0.0", name="ck_production_steps_per_unit_hours"),
    )
    op.create_index("ix_production_steps_specification_id", "production_steps", ["specification_id"])

    # 5. Add nullable specification_id column and index to production_orders
    op.add_column(
        "production_orders",
        sa.Column(
            "specification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_specifications.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_production_orders_specification_id", "production_orders", ["specification_id"])


def downgrade() -> None:
    # 1. Drop production_orders specification_id column and index
    op.drop_index("ix_production_orders_specification_id", table_name="production_orders")
    op.drop_column("production_orders", "specification_id")

    # 2. Drop production_steps table
    op.drop_index("ix_production_steps_specification_id", table_name="production_steps")
    op.drop_table("production_steps")

    # 3. Drop production_gemstones table
    op.drop_index("ix_production_gemstones_specification_id", table_name="production_gemstones")
    op.drop_table("production_gemstones")

    # 4. Drop production_materials table
    op.drop_index("ix_production_materials_specification_id", table_name="production_materials")
    op.drop_table("production_materials")

    # 5. Drop production_specifications table
    op.drop_index("ix_production_specifications_design_version", table_name="production_specifications")
    op.drop_index("ix_production_specifications_status", table_name="production_specifications")
    op.drop_index("ix_production_specifications_render_id", table_name="production_specifications")
    op.drop_index("ix_production_specifications_design_id", table_name="production_specifications")
    op.drop_index("ix_production_specifications_user_id", table_name="production_specifications")
    op.drop_table("production_specifications")
