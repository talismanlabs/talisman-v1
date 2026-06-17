"""Tests for idempotent SQLite schema initialization (slice S04.01)."""

import sqlite3
from pathlib import Path

from talisman_core.adapters.sqlite.migrations import initialize_database

EXPECTED_TABLES = {
    "projects",
    "lessons",
    "lesson_audit",
    "gate_events",
    "scheduler_events",
    "events",
}


def test_initialize_database_creates_expected_tables(tmp_path: Path) -> None:
    """A fresh database gets every TalisMan table from the schema."""
    db_path = tmp_path / "state" / "TalisMan.sqlite3"
    initialize_database(db_path)
    with sqlite3.connect(db_path) as conn:
        names = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert EXPECTED_TABLES <= names


def test_initialize_database_is_idempotent_and_preserves_data(tmp_path: Path) -> None:
    """Re-initializing an existing database does not error or drop data."""
    db_path = tmp_path / "state" / "TalisMan.sqlite3"
    initialize_database(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO projects (project_id, name, tier, status) VALUES (?, ?, ?, ?)",
            ("p1", "Demo", "lightweight", "created"),
        )
        conn.commit()

    initialize_database(db_path)  # second run must be a no-op for existing tables

    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    assert count == 1
