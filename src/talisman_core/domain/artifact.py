"""The Artifact domain model.

An artifact is an auditable output a project produces — a plan, a transcript, a
review, a retrospective. The domain records identity, kind, location, and a short
summary. Persisting or transmitting artifacts is the job of adapters; the domain
stays free of storage concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Artifact:
    """Immutable reference to an output produced during a project."""

    artifact_id: str
    project_id: str
    kind: str
    path: Path
    summary: str
