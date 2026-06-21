"""SQLite-backed memory store: structured lessons + project retrospectives (slice S16.13).

Implements ``MemoryPort`` against the shared state database so a lesson recorded at the end
of one project is durably retrievable — and surfaced at intake — for future projects
(AT-17). SQLite is infrastructure, so this adapter lives in the adapters layer; core code
depends only on ``MemoryPort`` and never imports ``sqlite3`` directly.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, cast

from talisman_core.adapters.sqlite.migrations import initialize_database
from talisman_core.ports.memory import (
    Lesson,
    LessonQuery,
    LessonSeverity,
    LessonStatus,
    MemoryPort,
    Retrospective,
)

_UPSERT_LESSON_SQL = """
INSERT INTO lessons
    (lesson_id, project_id, domain_tags, severity, statement, detail_ref, status, date,
     supersedes_lesson_id)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(lesson_id) DO UPDATE SET
    project_id=excluded.project_id, domain_tags=excluded.domain_tags,
    severity=excluded.severity, statement=excluded.statement, detail_ref=excluded.detail_ref,
    status=excluded.status, date=excluded.date,
    supersedes_lesson_id=excluded.supersedes_lesson_id, updated_at=CURRENT_TIMESTAMP
"""

_SELECT_LESSONS_BY_STATUS_SQL = """
SELECT lesson_id, project_id, domain_tags, severity, statement, detail_ref, status, date,
       supersedes_lesson_id
FROM lessons
WHERE status = ?
ORDER BY date DESC, lesson_id
"""

_UPSERT_RETRO_SQL = """
INSERT INTO retrospectives (project_id, content, lesson_ids)
VALUES (?, ?, ?)
ON CONFLICT(project_id) DO UPDATE SET
    content=excluded.content, lesson_ids=excluded.lesson_ids, updated_at=CURRENT_TIMESTAMP
"""

_SELECT_RETRO_SQL = (
    "SELECT project_id, content, lesson_ids FROM retrospectives WHERE project_id = ?"
)

_LessonRow = tuple[str, str, str, str, str, str, str, str, str | None]
_RetroRow = tuple[str, str, str]


class SQLiteMemoryStore:
    """Record and retrieve lessons + retrospectives in the shared SQLite state database."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the memory adapter and ensure the schema exists."""
        self._db_path = db_path
        initialize_database(db_path)

    def record_lesson(self, lesson: Lesson) -> None:
        """Persist (or update) a structured lesson for future retrieval."""
        connection = sqlite3.connect(self._db_path)
        try:
            connection.execute(
                _UPSERT_LESSON_SQL,
                (
                    lesson.lesson_id,
                    lesson.project_id,
                    json.dumps(list(lesson.domain_tags)),
                    lesson.severity.value,
                    lesson.statement,
                    str(lesson.detail_ref),
                    lesson.status.value,
                    lesson.lesson_date.isoformat(),
                    lesson.supersedes_lesson_id,
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def retrieve_lessons(self, query: LessonQuery) -> tuple[Lesson, ...]:
        """Retrieve lessons matching the query (status, optional project/domain), newest first."""
        connection = sqlite3.connect(self._db_path)
        try:
            rows = connection.execute(
                _SELECT_LESSONS_BY_STATUS_SQL, (query.status.value,)
            ).fetchall()
        finally:
            connection.close()

        lessons = [_lesson_from_row(row) for row in rows]
        if query.project_id is not None:
            lessons = [item for item in lessons if item.project_id == query.project_id]
        if query.domain_tags:
            wanted = set(query.domain_tags)
            lessons = [item for item in lessons if wanted.intersection(item.domain_tags)]
        return tuple(lessons[: max(0, query.limit)])

    def record_retrospective(self, retrospective: Retrospective) -> None:
        """Persist (or replace) a project's narrative retrospective."""
        connection = sqlite3.connect(self._db_path)
        try:
            connection.execute(
                _UPSERT_RETRO_SQL,
                (
                    retrospective.project_id,
                    retrospective.content,
                    json.dumps(list(retrospective.lesson_ids)),
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def load_retrospective(self, project_id: str) -> Retrospective | None:
        """Load a project's retrospective, if one was recorded."""
        connection = sqlite3.connect(self._db_path)
        try:
            row = connection.execute(_SELECT_RETRO_SQL, (project_id,)).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        loaded_project_id, content, lesson_ids = cast(_RetroRow, row)
        return Retrospective(
            project_id=loaded_project_id,
            content=content,
            lesson_ids=tuple(json.loads(lesson_ids)),
        )


def _lesson_from_row(row: object) -> Lesson:
    (
        lesson_id,
        project_id,
        domain_tags,
        severity,
        statement,
        detail_ref,
        status,
        lesson_date,
        supersedes,
    ) = cast(_LessonRow, row)
    return Lesson(
        lesson_id=lesson_id,
        project_id=project_id,
        domain_tags=tuple(json.loads(domain_tags)),
        severity=LessonSeverity(severity),
        statement=statement,
        detail_ref=Path(detail_ref),
        status=LessonStatus(status),
        lesson_date=date.fromisoformat(lesson_date),
        supersedes_lesson_id=supersedes,
    )


if TYPE_CHECKING:
    # Compile-time guarantee that the store satisfies the MemoryPort protocol.
    _memory_port_impl: type[MemoryPort] = SQLiteMemoryStore
