"""Tests for SQLite approval idempotency persistence."""

import sqlite3
from pathlib import Path

from talisman_core.adapters.sqlite.approval_idempotency import (
    ApprovalOutcome,
    SQLiteApprovalIdempotency,
)


def test_duplicate_idempotency_key_advances_once(tmp_path: Path) -> None:
    """A repeated approval key is persisted once and advances state once."""
    db_path = tmp_path / "state" / "TalisMan.sqlite3"
    approvals = SQLiteApprovalIdempotency(db_path)
    advanced_count = 0
    outcomes: list[ApprovalOutcome] = []

    for _ in range(2):
        outcome = approvals.record_and_advance(
            project_id="project-a",
            gate_id="project-a:plan",
            idempotency_key="project-a:plan:key-1",
            state="approved",
            current_pending_gate_id="project-a:plan",
        )
        outcomes.append(outcome)
        if outcome is ApprovalOutcome.ADVANCED:
            advanced_count += 1

    assert outcomes == [ApprovalOutcome.ADVANCED, ApprovalOutcome.DUPLICATE]
    assert advanced_count == 1
    assert _count_gate_events_for_key(db_path, "project-a:plan:key-1") == 1


def test_distinct_idempotency_keys_both_advance(tmp_path: Path) -> None:
    """Separate approval request keys are separate accepted events."""
    db_path = tmp_path / "state" / "TalisMan.sqlite3"
    approvals = SQLiteApprovalIdempotency(db_path)

    first = approvals.record_and_advance(
        project_id="project-a",
        gate_id="project-a:plan",
        idempotency_key="project-a:plan:key-1",
        state="approved",
        current_pending_gate_id="project-a:plan",
    )
    second = approvals.record_and_advance(
        project_id="project-a",
        gate_id="project-a:plan",
        idempotency_key="project-a:plan:key-2",
        state="approved",
        current_pending_gate_id="project-a:plan",
    )

    assert first is ApprovalOutcome.ADVANCED
    assert second is ApprovalOutcome.ADVANCED
    assert _count_gate_events(db_path) == 2


def test_non_pending_gate_is_ignored_without_insert(tmp_path: Path) -> None:
    """A stale or reordered approval for a non-pending gate is not recorded."""
    db_path = tmp_path / "state" / "TalisMan.sqlite3"
    approvals = SQLiteApprovalIdempotency(db_path)

    outcome = approvals.record_and_advance(
        project_id="project-a",
        gate_id="project-a:plan",
        idempotency_key="project-a:plan:key-1",
        state="approved",
        current_pending_gate_id="project-a:review",
    )

    assert outcome is ApprovalOutcome.IGNORED
    assert _count_gate_events(db_path) == 0


def _count_gate_events(db_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("SELECT COUNT(*) FROM gate_events").fetchone()
    if row is None:
        raise RuntimeError("SQLite did not return a gate_events count.")
    return int(row[0])


def _count_gate_events_for_key(db_path: Path, idempotency_key: str) -> int:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM gate_events WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
    if row is None:
        raise RuntimeError("SQLite did not return a gate_events count.")
    return int(row[0])
