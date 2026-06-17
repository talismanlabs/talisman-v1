"""SQLite-backed append-only project event log.

The event log is infrastructure-local in this slice: it persists auditable project
events in SQLite without introducing a new core port or changing workflow code.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from talisman_core.adapters.sqlite.migrations import initialize_database

_SELECT_EVENT_BY_ID_SQL = """
SELECT event_id, project_id, event_type, payload, created_at
FROM events
WHERE event_id = ?
"""
_SELECT_EVENTS_BY_PROJECT_SQL = """
SELECT event_id, project_id, event_type, payload, created_at
FROM events
WHERE project_id = ?
ORDER BY event_id
"""
_EventRow = tuple[int, str, str, str | None, str]


@dataclass(frozen=True, slots=True)
class EventRecord:
    """A persisted project event row."""

    event_id: int
    project_id: str
    event_type: str
    payload: str | None
    created_at: str


class SQLiteEventLog:
    """Append and query project events in the shared SQLite state database."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the event log adapter and ensure the schema exists."""
        self._db_path = db_path
        initialize_database(db_path)

    def append_event(
        self,
        project_id: str,
        event_type: str,
        payload: str | None = None,
    ) -> EventRecord:
        """Persist one event and return its stored row."""
        connection = sqlite3.connect(self._db_path)
        try:
            cursor = connection.execute(
                "INSERT INTO events (project_id, event_type, payload) VALUES (?, ?, ?)",
                (project_id, event_type, payload),
            )
            event_id = cursor.lastrowid
            if event_id is None:
                raise RuntimeError("SQLite did not report an event id after insert.")

            row = connection.execute(
                _SELECT_EVENT_BY_ID_SQL,
                (event_id,),
            ).fetchone()
            connection.commit()
        finally:
            connection.close()

        if row is None:
            raise RuntimeError(f"Inserted event {event_id} could not be reloaded.")
        return _event_from_row(row)

    def list_events(self, project_id: str) -> list[EventRecord]:
        """Return events for one project ordered by insertion id."""
        connection = sqlite3.connect(self._db_path)
        try:
            rows = connection.execute(
                _SELECT_EVENTS_BY_PROJECT_SQL,
                (project_id,),
            ).fetchall()
        finally:
            connection.close()

        return [_event_from_row(row) for row in rows]


def _event_from_row(row: object) -> EventRecord:
    event_id, project_id, event_type, payload, created_at = cast(_EventRow, row)
    return EventRecord(
        event_id=event_id,
        project_id=project_id,
        event_type=event_type,
        payload=payload,
        created_at=created_at,
    )
