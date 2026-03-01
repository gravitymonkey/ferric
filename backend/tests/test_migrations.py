from __future__ import annotations

import os
import subprocess
from pathlib import Path

from sqlalchemy import create_engine, inspect


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_alembic(database_url: str, command: list[str]) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    subprocess.run(
        ["python3", "-m", "alembic", "-c", "backend/alembic.ini", *command],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_alembic_upgrade_and_downgrade_sqlite(tmp_path) -> None:
    db_path = tmp_path / "migration_test.db"
    database_url = f"sqlite:///{db_path}"

    _run_alembic(database_url, ["upgrade", "head"])
    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert "playback_sessions" in inspector.get_table_names()
    assert "tracks" in inspector.get_table_names()
    assert "track_artwork" in inspector.get_table_names()
    assert "track_streams" in inspector.get_table_names()
    assert "listening_events" in inspector.get_table_names()
    assert "track_metadata" in inspector.get_table_names()
    track_columns = {col["name"] for col in inspector.get_columns("tracks")}
    assert "uploaded_at" in track_columns
    engine.dispose()

    _run_alembic(database_url, ["downgrade", "base"])
    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert "playback_sessions" not in inspector.get_table_names()
    engine.dispose()
