"""Tests for system health aggregation (slice S12.01)."""

from talisman_core.observability.health import (
    ComponentHealth,
    HealthState,
    SystemHealth,
    aggregate_health,
)


def test_empty_is_ok() -> None:
    """With nothing known to be wrong, the system reports OK."""
    assert aggregate_health([]).overall is HealthState.OK


def test_all_ok_is_ok() -> None:
    """All-healthy components aggregate to OK."""
    health = aggregate_health(
        [
            ComponentHealth("gateway", HealthState.OK),
            ComponentHealth("scheduler", HealthState.OK),
        ]
    )
    assert health.overall is HealthState.OK


def test_worst_component_wins() -> None:
    """A single DOWN component drives the overall status to DOWN, not hidden by OK ones."""
    health = aggregate_health(
        [
            ComponentHealth("gateway", HealthState.OK),
            ComponentHealth("scheduler", HealthState.DEGRADED),
            ComponentHealth("database", HealthState.DOWN),
        ]
    )
    assert health.overall is HealthState.DOWN


def test_degraded_without_down() -> None:
    """Degraded is reported when present and nothing is worse."""
    health = aggregate_health(
        [
            ComponentHealth("gateway", HealthState.OK),
            ComponentHealth("scheduler", HealthState.DEGRADED),
        ]
    )
    assert health.overall is HealthState.DEGRADED


def test_to_dict_status_payload() -> None:
    """The /status payload carries the overall status and each component."""
    health = SystemHealth(
        overall=HealthState.DEGRADED,
        components=(ComponentHealth("gateway", HealthState.DEGRADED, "slow"),),
    )
    payload = health.to_dict()
    assert payload["status"] == "degraded"
    assert payload["components"] == [{"name": "gateway", "status": "degraded", "detail": "slow"}]
