"""Idempotent SQLite schema initialization for TalisMan state (slice S04.01).

The shared state database is created and migrated from the declarative schema in
``schema.sql``. Initialization is idempotent — every statement uses
``CREATE TABLE IF NOT EXISTS`` — so it is safe to run on every startup without
disturbing existing data.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def initialize_database(db_path: Path) -> None:
    """Create the state database (and parent directory) and apply the schema.

    Safe to call repeatedly: ``schema.sql`` is idempotent, so existing tables and
    rows are preserved. Raises the underlying ``sqlite3.Error`` if the database
    cannot be opened or the schema cannot be applied.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(schema_sql)
        connection.commit()
    finally:
        connection.close()
