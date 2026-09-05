"""004 — image_favorites and image_shares tables

Revision ID: 004
Revises: 003
Create Date: 2026-07-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "004"
down_revision = "003_prompt_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "image_favorites",
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("image_id", UUID(as_uuid=False), sa.ForeignKey("images.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "image_shares",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("image_id", UUID(as_uuid=False), sa.ForeignKey("images.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shared_by", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("share_token", sa.String(64), unique=True, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("view_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_image_shares_share_token", "image_shares", ["share_token"], unique=True)
    op.create_index("ix_image_shares_image_id", "image_shares", ["image_id"])


def downgrade() -> None:
    op.drop_table("image_shares")
    op.drop_table("image_favorites")
