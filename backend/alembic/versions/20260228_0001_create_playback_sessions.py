"""create playback_sessions table

Revision ID: 20260228_0001
Revises:
Create Date: 2026-02-28 20:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260228_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playback_sessions",
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("queue_track_ids_json", sa.Text(), nullable=False),
        sa.Column("current_track_id", sa.String(length=64), nullable=False),
        sa.Column("position_sec", sa.Integer(), nullable=False),
        sa.Column("shuffle", sa.Boolean(), nullable=False),
        sa.Column("repeat_mode", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("session_id"),
    )


def downgrade() -> None:
    op.drop_table("playback_sessions")
