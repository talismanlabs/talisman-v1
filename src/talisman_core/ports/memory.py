"""Memory port for structured lessons and narrative project retrospectives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Protocol


class LessonSeverity(str, Enum):
    """Severity assigned to a structured lesson."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LessonStatus(str, Enum):
    """Lifecycle state of a structured lesson."""

    ACTIVE = "active"
    RETRACTED = "retracted"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class Lesson:
    """Structured lesson that can be retrieved for future projects."""

    lesson_id: str
    project_id: str
    domain_tags: tuple[str, ...]
    severity: LessonSeverity
    statement: str
    detail_ref: Path
    status: LessonStatus
    lesson_date: date
    supersedes_lesson_id: str | None = None


@dataclass(frozen=True)
class LessonQuery:
    """Query used to retrieve lessons relevant to a project or domain."""

    project_id: str | None = None
    domain_tags: tuple[str, ...] = ()
    status: LessonStatus = LessonStatus.ACTIVE
    limit: int = 10


@dataclass(frozen=True)
class Retrospective:
    """Narrative retrospective captured at the end of a project cycle."""

    project_id: str
    content: str
    lesson_ids: tuple[str, ...]


class MemoryPort(Protocol):
    """Interface for recording and retrieving lessons and retrospectives."""

    def record_lesson(self, lesson: Lesson) -> None:
        """Record a structured lesson for future retrieval."""
        ...

    def retrieve_lessons(self, query: LessonQuery) -> tuple[Lesson, ...]:
        """Retrieve lessons that match the supplied query."""
        ...

    def record_retrospective(self, retrospective: Retrospective) -> None:
        """Record a narrative project retrospective."""
        ...

    def load_retrospective(self, project_id: str) -> Retrospective | None:
        """Load a project retrospective, if one exists."""
        ...
