"""create track metadata table

Revision ID: 20260228_0004
Revises: 20260228_0003
Create Date: 2026-02-28 21:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260228_0004"
down_revision = "20260228_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "track_metadata",
        sa.Column("track_id", sa.String(length=64), nullable=False),
        sa.Column("analysis_version", sa.String(length=32), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sample_rate_hz", sa.Integer(), nullable=False),
        sa.Column("duration_sec", sa.Float(), nullable=False),
        sa.Column("tempo_bpm", sa.Float(), nullable=True),
        sa.Column("beat_count", sa.Integer(), nullable=True),
        sa.Column("onset_strength_mean", sa.Float(), nullable=True),
        sa.Column("rms_mean", sa.Float(), nullable=True),
        sa.Column("rms_std", sa.Float(), nullable=True),
        sa.Column("spectral_centroid_mean", sa.Float(), nullable=True),
        sa.Column("spectral_centroid_std", sa.Float(), nullable=True),
        sa.Column("spectral_bandwidth_mean", sa.Float(), nullable=True),
        sa.Column("spectral_rolloff_mean", sa.Float(), nullable=True),
        sa.Column("spectral_flatness_mean", sa.Float(), nullable=True),
        sa.Column("zero_crossing_rate_mean", sa.Float(), nullable=True),
        sa.Column("mfcc_mean_json", sa.Text(), nullable=True),
        sa.Column("chroma_mean_json", sa.Text(), nullable=True),
        sa.Column("tonnetz_mean_json", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("track_id"),
    )


def downgrade() -> None:
    op.drop_table("track_metadata")
