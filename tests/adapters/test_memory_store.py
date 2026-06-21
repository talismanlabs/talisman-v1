"""Tests for the SQLite memory store (slice S16.13, AT-17)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from talisman_core.adapters.sqlite.memory import SQLiteMemoryStore
from talisman_core.ports.memory import (
    Lesson,
    LessonQuery,
    LessonSeverity,
    LessonStatus,
    Retrospective,
)


def _lesson(
    lesson_id: str,
    *,
    domain_tags: tuple[str, ...] = ("ci",),
    status: LessonStatus = LessonStatus.ACTIVE,
    day: int = 1,
) -> Lesson:
    return Lesson(
        lesson_id=lesson_id,
        project_id="proj",
        domain_tags=domain_tags,
        severity=LessonSeverity.HIGH,
        statement=f"lesson {lesson_id}",
        detail_ref=Path(f"docs/lessons/{lesson_id}.md"),
        status=status,
        lesson_date=date(2026, 6, day),
    )


def test_record_and_retrieve_lesson_roundtrips_durably(tmp_path) -> None:
    """A recorded lesson is retrievable from a fresh store on the same database (durable)."""
    db = tmp_path / "state.sqlite3"
    SQLiteMemoryStore(db).record_lesson(_lesson("L1"))

    # A brand-new store handle on the same file (a fresh process would do the same).
    retrieved = SQLiteMemoryStore(db).retrieve_lessons(LessonQuery())

    assert [lesson.lesson_id for lesson in retrieved] == ["L1"]
    assert retrieved[0].statement == "lesson L1"
    assert retrieved[0].domain_tags == ("ci",)
    assert retrieved[0].severity is LessonSeverity.HIGH


def test_retrieve_filters_by_status_domain_and_limit(tmp_path) -> None:
    """Retrieval returns only active lessons, filtered by domain overlap and capped by limit."""
    store = SQLiteMemoryStore(tmp_path / "state.sqlite3")
    store.record_lesson(_lesson("active-ci", domain_tags=("ci", "build"), day=3))
    store.record_lesson(_lesson("active-sec", domain_tags=("security",), day=2))
    store.record_lesson(
        _lesson("retracted-ci", domain_tags=("ci",), status=LessonStatus.RETRACTED, day=1)
    )

    # Only active lessons whose domains overlap "ci" — the retracted one is excluded.
    ci = store.retrieve_lessons(LessonQuery(domain_tags=("ci",)))
    assert [lesson.lesson_id for lesson in ci] == ["active-ci"]

    # Active, any domain, newest first, capped at 1.
    capped = store.retrieve_lessons(LessonQuery(limit=1))
    assert [lesson.lesson_id for lesson in capped] == ["active-ci"]  # day=3 is newest


def test_record_lesson_is_idempotent_on_id(tmp_path) -> None:
    """Re-recording the same lesson id updates in place rather than duplicating."""
    store = SQLiteMemoryStore(tmp_path / "state.sqlite3")
    store.record_lesson(_lesson("L1"))
    store.record_lesson(_lesson("L1", domain_tags=("revised",)))

    retrieved = store.retrieve_lessons(LessonQuery())
    assert len(retrieved) == 1
    assert retrieved[0].domain_tags == ("revised",)


def test_retrospective_roundtrips(tmp_path) -> None:
    """A recorded retrospective is loadable; an unknown project returns None."""
    store = SQLiteMemoryStore(tmp_path / "state.sqlite3")
    store.record_retrospective(
        Retrospective(project_id="proj", content="went well", lesson_ids=("L1", "L2"))
    )

    loaded = store.load_retrospective("proj")
    assert loaded is not None
    assert loaded.content == "went well"
    assert loaded.lesson_ids == ("L1", "L2")
    assert store.load_retrospective("unknown") is None
