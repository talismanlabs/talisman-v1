"""State persistence port for projects, gates, and auditable gate events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from talisman_core.domain import Gate, GateStatus, Project


@dataclass(frozen=True)
class GateEvent:
    """Auditable record of a gate state transition."""

    project_id: str
    gate_id: str
    idempotency_key: str
    status: GateStatus
    summary: str


class StatePort(Protocol):
    """Interface for durable project, gate, and gate-event state."""

    def save_project(self, project: Project) -> None:
        """Persist the current project state."""
        ...

    def load_project(self, project_id: str) -> Project | None:
        """Load a project by identifier, if it exists."""
        ...

    def save_gate(self, gate: Gate) -> None:
        """Persist the current gate state."""
        ...

    def load_gate(self, project_id: str, gate_id: str) -> Gate | None:
        """Load a gate by project and gate identifier, if it exists."""
        ...

    def record_gate_event(self, event: GateEvent) -> None:
        """Append an auditable gate event."""
        ...

    def list_gate_events(
        self,
        project_id: str,
        gate_id: str | None = None,
    ) -> tuple[GateEvent, ...]:
        """List gate events for a project, optionally restricted to one gate."""
        ...
