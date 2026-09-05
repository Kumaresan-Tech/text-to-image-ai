"""007 — widen images.seed to BIGINT for full 32-bit random seeds

Revision ID: 007
Revises: 006
Create Date: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("images", "seed", existing_type=sa.Integer, type_=sa.BigInteger, existing_nullable=True)


def downgrade() -> None:
    op.alter_column("images", "seed", existing_type=sa.BigInteger, type_=sa.Integer, existing_nullable=True)
