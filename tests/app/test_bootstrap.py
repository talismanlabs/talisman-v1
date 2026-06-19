"""Tests for the bootstrap self-improvement run (slice S14.02)."""

from talisman_core.app.bootstrap import (
    PLANNING_PHASES,
    PROJECT_ID,
    run_self_improvement_spiral,
)


def test_spiral_completes_every_planning_phase() -> None:
    """The governed v1.1-planning spiral runs to completion through its gates."""
    result = run_self_improvement_spiral()
    assert result.final_state["completed_phases"] == list(PLANNING_PHASES)
    assert result.final_state["pending_gate_id"] is None


def test_gates_fire_through_the_approval_port() -> None:
    """Both gate phases interrupt and are resolved through the approval port, in order."""
    result = run_self_improvement_spiral()
    assert result.gates_fired == (f"{PROJECT_ID}:plan", f"{PROJECT_ID}:slice_approval")


def test_plan_phase_routes_through_the_worker_seam() -> None:
    """The plan phase produces its artifact via the injected WorkerPort (stub)."""
    result = run_self_improvement_spiral()
    assert any(artifact.startswith("plan:planned:") for artifact in result.final_state["artifacts"])


def test_v1_1_backlog_artifact_is_produced_with_real_items() -> None:
    """The run yields the v1.1 backlog markdown carrying the real improvement items."""
    result = run_self_improvement_spiral()
    assert "TalisMan v1.1 improvement backlog" in result.backlog_markdown
    assert "scoped-credentials" in result.backlog_markdown
    assert "lessons-retrieval" in result.backlog_markdown
