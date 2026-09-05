"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Users ─────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("provider_id", sa.String(255), nullable=True),
        sa.Column("credits", sa.Integer, server_default="50", nullable=False),
        sa.Column("plan", sa.String(50), server_default="FREE", nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── Plans ──────────────────────────────────────
    op.create_table(
        "plans",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("credits", sa.Integer, nullable=False),
        sa.Column("price_monthly", sa.Float, nullable=False),
        sa.Column("features", JSONB, nullable=True),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Images ─────────────────────────────────────
    op.create_table(
        "images",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("negative_prompt", sa.Text, nullable=True),
        sa.Column("image_url", sa.Text, nullable=False),
        sa.Column("thumbnail_url", sa.Text, nullable=True),
        sa.Column("width", sa.Integer, server_default="1024"),
        sa.Column("height", sa.Integer, server_default="1024"),
        sa.Column("steps", sa.Integer, server_default="30"),
        sa.Column("cfg_scale", sa.Float, server_default="7.5"),
        sa.Column("sampler", sa.String(100), server_default="DPM++ 2M Karras"),
        sa.Column("seed", sa.Integer, nullable=True),
        sa.Column("model", sa.String(100), server_default="sdxl-1.0"),
        sa.Column("is_public", sa.Boolean, server_default="false"),
        sa.Column("likes_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Jobs ───────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False, index=True),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("params", JSONB, nullable=True),
        sa.Column("image_id", UUID(as_uuid=False), sa.ForeignKey("images.id", ondelete="SET NULL"), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Image Tags ─────────────────────────────────
    op.create_table(
        "image_tags",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("image_id", UUID(as_uuid=False), sa.ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("tag", sa.String(100), nullable=False),
    )
    op.create_index("uq_image_tag", "image_tags", ["image_id", "tag"], unique=True)

    # ── User Likes ─────────────────────────────────
    op.create_table(
        "user_likes",
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("image_id", UUID(as_uuid=False), sa.ForeignKey("images.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("user_likes")
    op.drop_table("image_tags")
    op.drop_table("jobs")
    op.drop_table("images")
    op.drop_table("plans")
    op.drop_table("users")
