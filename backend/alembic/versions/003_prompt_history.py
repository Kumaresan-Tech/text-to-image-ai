"""add prompt history

Revision ID: 003_prompt_history
Revises: 002_auth
Create Date: 2024-01-03 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "003_prompt_history"
down_revision: Union[str, None] = "002_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_history",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("original_prompt", sa.Text, nullable=False),
        sa.Column("enhanced_prompt", sa.Text, nullable=True),
        sa.Column("negative_prompt", sa.Text, nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("model_target", sa.String(100), nullable=True),
        sa.Column("is_safe", sa.Boolean, server_default="true", nullable=False),
        sa.Column("safety_flags", JSONB, nullable=True),
        sa.Column("used", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_prompt_history_action", "prompt_history", ["action"])
    op.create_index("ix_prompt_history_created_at", "prompt_history", ["created_at"])


def downgrade() -> None:
    op.drop_table("prompt_history")
