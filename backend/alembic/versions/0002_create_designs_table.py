"""create designs table

Revision ID: 0002_create_designs
Revises: 0001_create_users
Create Date: 2026-09-01 20:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_create_designs"
down_revision: Union[str, None] = "0001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create designs table
    op.create_table(
        "designs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("sketch_image_url", sa.String(length=1024), nullable=True),
        sa.Column("rendered_image_url", sa.String(length=1024), nullable=True),
        sa.Column("ai_prompt", sa.Text(), nullable=True),
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
    op.create_index(op.f("ix_designs_id"), "designs", ["id"], unique=False)
    op.create_index(op.f("ix_designs_user_id"), "designs", ["user_id"], unique=False)
    op.create_index(op.f("ix_designs_name"), "designs", ["name"], unique=False)
    op.create_index(op.f("ix_designs_category"), "designs", ["category"], unique=False)
    op.create_index(op.f("ix_designs_status"), "designs", ["status"], unique=False)
    op.create_index(op.f("ix_designs_created_at"), "designs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_designs_created_at"), table_name="designs")
    op.drop_index(op.f("ix_designs_status"), table_name="designs")
    op.drop_index(op.f("ix_designs_category"), table_name="designs")
    op.drop_index(op.f("ix_designs_name"), table_name="designs")
    op.drop_index(op.f("ix_designs_user_id"), table_name="designs")
    op.drop_index(op.f("ix_designs_id"), table_name="designs")
    op.drop_table("designs")
