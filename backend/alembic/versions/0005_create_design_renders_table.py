"""create design renders table and link to production orders

Revision ID: 0005_create_design_renders_table
Revises: 0004_create_production_schedules_table
Create Date: 2026-09-19 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_create_design_renders_table"
down_revision: Union[str, None] = "0004_create_production_schedules_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create design_renders table
    op.create_table(
        "design_renders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "design_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("designs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "parent_render_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("design_renders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("render_mode", sa.String(length=50), nullable=False, server_default="text"),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("enhanced_prompt", sa.Text(), nullable=True),
        sa.Column("structured_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("image_url", sa.String(length=1024), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("control_type", sa.String(length=50), nullable=False, server_default="none"),
        sa.Column("control_strength", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column(
            "is_approved_for_production",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
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
    )

    # 2. Add indexes on design_renders
    op.create_index("ix_design_renders_design_id", "design_renders", ["design_id"])
    op.create_index("ix_design_renders_user_id", "design_renders", ["user_id"])
    op.create_index("ix_design_renders_version_number", "design_renders", ["version_number"])
    op.create_index("ix_design_renders_is_approved", "design_renders", ["is_approved_for_production"])
    op.create_index(
        "ix_design_renders_design_version",
        "design_renders",
        ["design_id", "version_number"],
    )

    # 3. Add columns to production_orders
    op.add_column(
        "production_orders",
        sa.Column(
            "render_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("design_renders.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "production_orders",
        sa.Column("approved_render_url", sa.String(length=1024), nullable=True),
    )
    op.create_index("ix_production_orders_render_id", "production_orders", ["render_id"])

    # 4. Safe backward-compatible data backfill:
    # Existing designs with rendered_image_url get a V1 DesignRender record.
    op.execute(
        """
        INSERT INTO design_renders (
            id, design_id, user_id, version_number, render_mode,
            prompt, image_url, is_approved_for_production, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            id,
            user_id,
            1,
            'text',
            COALESCE(NULLIF(ai_prompt, ''), name),
            rendered_image_url,
            false,
            created_at,
            updated_at
        FROM designs
        WHERE rendered_image_url IS NOT NULL AND rendered_image_url != ''
        """
    )


def downgrade() -> None:
    # 1. Remove production_orders columns & index
    op.drop_index("ix_production_orders_render_id", table_name="production_orders")
    op.drop_column("production_orders", "approved_render_url")
    op.drop_column("production_orders", "render_id")

    # 2. Drop design_renders indexes
    op.drop_index("ix_design_renders_design_version", table_name="design_renders")
    op.drop_index("ix_design_renders_is_approved", table_name="design_renders")
    op.drop_index("ix_design_renders_version_number", table_name="design_renders")
    op.drop_index("ix_design_renders_user_id", table_name="design_renders")
    op.drop_index("ix_design_renders_design_id", table_name="design_renders")

    # 3. Drop design_renders table
    op.drop_table("design_renders")
