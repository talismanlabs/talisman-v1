"""Tests for pure systemd unit rendering (slice S13.01)."""

import re
from pathlib import Path

from talisman_core.app.systemd_units import (
    SystemdUnitConfig,
    render_gateway_unit,
    render_orchestrator_unit,
    render_systemd_units,
)


API_KEY_LIKE_ASSIGNMENT = re.compile(r"=(?:[A-Za-z0-9_-]{24,}|[A-Za-z0-9_-]*-[A-Za-z0-9_-]{20,})")


def test_gateway_unit_restarts_and_installs_under_default_target() -> None:
    """The gateway unit auto-restarts and installs into the default user target."""
    unit = render_gateway_unit()

    assert "Restart=on-failure\n" in unit
    assert "\n[Install]\nWantedBy=default.target\n" in unit


def test_orchestrator_unit_restarts_after_gateway_unit() -> None:
    """The orchestrator restarts and explicitly orders itself after the gateway."""
    unit = render_orchestrator_unit(SystemdUnitConfig(gateway_unit_name="custom-gateway.service"))

    assert "Restart=on-failure\n" in unit
    assert "After=custom-gateway.service\n" in unit
    assert "Wants=custom-gateway.service\n" in unit


def test_rendered_units_do_not_embed_secret_like_assignments() -> None:
    """Rendered units reference paths and environment names without embedding secret values."""
    rendered = render_systemd_units()
    combined = rendered.gateway_unit + rendered.orchestrator_unit

    assert "Environment=TALISMAN_HOME=%h/TalisMan\n" in rendered.gateway_unit
    assert "Environment=PYTHONUNBUFFERED=1\n" in rendered.orchestrator_unit
    assert API_KEY_LIKE_ASSIGNMENT.search(combined) is None


def test_rendering_is_deterministic_for_same_config() -> None:
    """Rendering the same config twice produces identical unit filenames and contents."""
    config = SystemdUnitConfig(gateway_unit_name="talisman-gateway.service")

    assert render_systemd_units(config) == render_systemd_units(config)


def test_deploy_reference_units_match_default_renderer() -> None:
    """Committed operator reference units stay in sync with the default renderer."""
    repo_root = Path(__file__).resolve().parents[2]
    deploy_dir = repo_root / "deploy" / "systemd"
    rendered = render_systemd_units()

    assert (deploy_dir / rendered.gateway_unit_name).read_text(
        encoding="utf-8"
    ) == rendered.gateway_unit
    assert (deploy_dir / rendered.orchestrator_unit_name).read_text(
        encoding="utf-8"
    ) == rendered.orchestrator_unit
