"""Tests for the application composition root (slice S14.01)."""

from talisman_core.app.composition import TalismanApp, build_application


def test_build_application_assembles_a_runnable_app() -> None:
    """The composition root returns a wired app with a compiled graph and scheduler."""
    app = build_application()
    assert isinstance(app, TalismanApp)
    assert app.graph is not None
    assert app.scheduler.active_count == 0


def test_run_project_completes_a_non_gated_cycle() -> None:
    """A non-gated spiral runs every requested phase and records its artifacts."""
    logs: list[str] = []
    app = build_application(log_sink=logs.append)
    final = app.run_project("p1", ["discovery", "plan"])
    assert final["completed_phases"] == ["discovery", "plan"]
    assert final["artifacts"] == ["discovery:p1", "plan:p1"]
    assert any("project_finished" in line for line in logs)


def test_run_project_is_deterministic() -> None:
    """Two fresh assemblies produce identical results for the same project."""
    app1 = build_application(log_sink=lambda _line: None)
    app2 = build_application(log_sink=lambda _line: None)
    first = app1.run_project("p", ["discovery", "synthesis"])
    second = app2.run_project("p", ["discovery", "synthesis"])
    assert first["artifacts"] == second["artifacts"]
    assert first["completed_phases"] == second["completed_phases"]


def test_only_sequenced_phases_run() -> None:
    """Phases absent from the sequence are never entered (tiering lives in policy)."""
    app = build_application(log_sink=lambda _line: None)
    final = app.run_project("p2", ["plan"])
    assert final["completed_phases"] == ["plan"]
    assert final["artifacts"] == ["plan:p2"]
