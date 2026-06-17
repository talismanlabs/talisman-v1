"""Tests for the SQLite project event log adapter."""

from pathlib import Path

from talisman_core.adapters.sqlite.event_log import SQLiteEventLog


def test_events_persist_across_connections_and_can_be_queried_by_project(
    tmp_path: Path,
) -> None:
    """Events written through one adapter instance are readable through another."""
    db_path = tmp_path / "state" / "TalisMan.sqlite3"
    writer = SQLiteEventLog(db_path)
    stored = writer.append_event(
        project_id="project-a",
        event_type="slice_started",
        payload='{"slice_id":"S04.02"}',
    )
    writer.append_event(
        project_id="project-b",
        event_type="slice_started",
        payload=None,
    )

    reader = SQLiteEventLog(db_path)
    events = reader.list_events("project-a")

    assert events == [stored]
    assert events[0].event_id > 0
    assert events[0].created_at


def test_events_for_different_projects_are_isolated(tmp_path: Path) -> None:
    """Project queries return only events for the requested project."""
    db_path = tmp_path / "state" / "TalisMan.sqlite3"
    event_log = SQLiteEventLog(db_path)
    event_log.append_event("project-a", "slice_started", "first")
    event_log.append_event("project-b", "slice_started", "second")
    event_log.append_event("project-a", "slice_finished", "third")

    project_a_events = event_log.list_events("project-a")
    project_b_events = event_log.list_events("project-b")

    assert [event.event_type for event in project_a_events] == [
        "slice_started",
        "slice_finished",
    ]
    assert [event.payload for event in project_a_events] == ["first", "third"]
    assert [event.event_type for event in project_b_events] == ["slice_started"]
    assert [event.payload for event in project_b_events] == ["second"]


def test_event_ordering_is_stable_by_event_id(tmp_path: Path) -> None:
    """Events are returned in insertion order for the selected project."""
    db_path = tmp_path / "state" / "TalisMan.sqlite3"
    event_log = SQLiteEventLog(db_path)
    first = event_log.append_event("project-a", "first", None)
    event_log.append_event("project-b", "other-project", None)
    second = event_log.append_event("project-a", "second", None)
    third = event_log.append_event("project-a", "third", None)

    events = event_log.list_events("project-a")

    assert events == [first, second, third]
    assert [event.event_id for event in events] == sorted(event.event_id for event in events)
