"""System health and status reporting (slice S12.01).

Aggregates per-component health into an overall system status the operator can read
via ``/status``. The overall status is the worst component status (OK < DEGRADED < DOWN),
so a single failing component is never hidden behind healthy ones.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum


class HealthState(str, Enum):
    """Health of a component, or of the system as a whole when aggregated."""

    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


_SEVERITY: dict[HealthState, int] = {
    HealthState.OK: 0,
    HealthState.DEGRADED: 1,
    HealthState.DOWN: 2,
}


@dataclass(frozen=True)
class ComponentHealth:
    """Health of a single named component (e.g. gateway, scheduler, database)."""

    name: str
    state: HealthState
    detail: str = ""


@dataclass(frozen=True)
class SystemHealth:
    """Aggregated health across all reported components."""

    overall: HealthState
    components: tuple[ComponentHealth, ...]

    def to_dict(self) -> dict[str, object]:
        """Render the status payload exposed by ``/status``."""
        return {
            "status": self.overall.value,
            "components": [
                {"name": c.name, "status": c.state.value, "detail": c.detail}
                for c in self.components
            ],
        }


def aggregate_health(components: Iterable[ComponentHealth]) -> SystemHealth:
    """Combine component health into a system status.

    The overall status is the worst component status; an empty set of components is
    reported as OK (nothing is known to be wrong).
    """
    items = tuple(components)
    overall = HealthState.OK
    for component in items:
        if _SEVERITY[component.state] > _SEVERITY[overall]:
            overall = component.state
    return SystemHealth(overall=overall, components=items)
