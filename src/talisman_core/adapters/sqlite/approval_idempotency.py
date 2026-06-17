"""SQLite-backed approval idempotency guard.

Approval duplicate suppression is durable state: the ``gate_events`` table owns
the unique ``idempotency_key`` constraint, and this adapter treats that
constraint as the source of truth for whether an approval may advance state.
"""

from __future__ import annotations

import sqlite3
from enum import Enum
from pathlib import Path

from talisman_core.adapters.sqlite.migrations import initialize_database

_INSERT_GATE_EVENT_SQL = """
INSERT INTO gate_events (project_id, gate_name, idempotency_key, state)
VALUES (?, ?, ?, ?)
"""


class ApprovalOutcome(str, Enum):
    """Result of attempting to apply an approval idempotently."""

    ADVANCED = "advanced"
    DUPLICATE = "duplicate"
    IGNORED = "ignored"


class SQLiteApprovalIdempotency:
    """Record approval gate events once in the shared SQLite state database."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the guard and ensure the gate-events schema exists."""
        self._db_path = db_path
        initialize_database(db_path)

    def record_and_advance(
        self,
        *,
        project_id: str,
        gate_id: str,
        idempotency_key: str,
        state: str,
        current_pending_gate_id: str | None,
    ) -> ApprovalOutcome:
        """Record an approval once and return whether the caller may advance state.

        ``IGNORED`` is returned before any database write when ``gate_id`` is not
        the current pending gate. ``ADVANCED`` is returned only for the first
        successful insert of ``idempotency_key``. Duplicate keys are rejected by
        SQLite's unique constraint and reported as ``DUPLICATE`` without any
        state-advance permission.
        """
        if current_pending_gate_id != gate_id:
            return ApprovalOutcome.IGNORED

        connection = sqlite3.connect(self._db_path)
        try:
            try:
                connection.execute(
                    _INSERT_GATE_EVENT_SQL,
                    (project_id, gate_id, idempotency_key, state),
                )
            except sqlite3.IntegrityError as error:
                connection.rollback()
                if _is_unique_constraint_error(error):
                    return ApprovalOutcome.DUPLICATE
                raise

            connection.commit()
        finally:
            connection.close()

        return ApprovalOutcome.ADVANCED


def _is_unique_constraint_error(error: sqlite3.IntegrityError) -> bool:
    error_code = getattr(error, "sqlite_errorcode", None)
    return isinstance(error_code, int) and error_code == sqlite3.SQLITE_CONSTRAINT_UNIQUE
