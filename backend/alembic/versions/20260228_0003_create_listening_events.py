"""create listening events table

Revision ID: 20260228_0003
Revises: 20260228_0002
Create Date: 2026-02-28 21:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260228_0003"
down_revision = "20260228_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listening_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("track_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("position_sec", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listening_events_user_id", "listening_events", ["user_id"], unique=False)
    op.create_index("ix_listening_events_track_id", "listening_events", ["track_id"], unique=False)
    op.create_index("ix_listening_events_action", "listening_events", ["action"], unique=False)
    op.create_index("ix_listening_events_created_at", "listening_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_listening_events_created_at", table_name="listening_events")
    op.drop_index("ix_listening_events_action", table_name="listening_events")
    op.drop_index("ix_listening_events_track_id", table_name="listening_events")
    op.drop_index("ix_listening_events_user_id", table_name="listening_events")
    op.drop_table("listening_events")
