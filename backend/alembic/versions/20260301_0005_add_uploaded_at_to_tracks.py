"""add uploaded_at to tracks

Revision ID: 20260301_0005
Revises: 20260228_0004
Create Date: 2026-03-01 17:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260301_0005"
down_revision = "20260228_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tracks", sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("tracks", "uploaded_at")
