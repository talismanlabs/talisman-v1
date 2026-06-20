"""Tests for the generic project intake (slice S16.09).

These prove project-agnosticism: a brand-new project — not TalisMan's own bootstrap — runs
end to end through the governed spiral, with its own phases and gates, deterministically.
"""

from __future__ import annotations

from talisman_core.app.project_run import ProjectRunResult, ProjectSpec, run_project
from talisman_core.ports.approval import ApprovalDecision, ApprovalRequest


def test_runs_a_brand_new_greenfield_project_end_to_end() -> None:
    """A new project with its own phases + gate completes through the governed spiral."""
    spec = ProjectSpec(
        project_id="greenfield-demo",
        phases=("interview", "plan", "review"),
        gate_phases=frozenset({"plan"}),
    )

    result = run_project(spec)

    assert isinstance(result, ProjectRunResult)
    assert result.final_state["project_id"] == "greenfield-demo"
    assert result.final_state["completed_phases"] == ["interview", "plan", "review"]
    assert result.gates_fired == ("greenfield-demo:plan",)


def test_a_different_spec_with_different_phases_and_no_gates_also_runs() -> None:
    """The intake is generic, not hardcoded: a different project shape runs just as well."""
    spec = ProjectSpec(project_id="another-project", phases=("discovery", "synthesis"))

    result = run_project(spec)

    assert result.final_state["completed_phases"] == ["discovery", "synthesis"]
    assert result.gates_fired == ()  # no gates configured for this project


def test_a_custom_approval_channel_plugs_into_the_same_seam() -> None:
    """A real approval channel injects through ``approver`` (here a recording auto-approver)."""

    class _Approver:
        def __init__(self) -> None:
            self.seen: list[str] = []

        def request_approval(self, request: ApprovalRequest) -> ApprovalDecision:
            self.seen.append(request.gate_id)
            return ApprovalDecision.APPROVE

    approver = _Approver()
    spec = ProjectSpec("p-x", ("interview", "plan", "review"), frozenset({"plan"}))

    result = run_project(spec, approver=approver)

    assert approver.seen == ["p-x:plan"]
    assert result.gates_fired == ("p-x:plan",)
    assert result.final_state["completed_phases"] == ["interview", "plan", "review"]


def test_a_project_close_produces_a_retrospective() -> None:
    """Every run produces a markdown retrospective at close (AT-16)."""
    spec = ProjectSpec("retro-demo", ("interview", "plan", "review"), frozenset({"plan"}))

    result = run_project(spec)

    retro = result.retrospective
    assert "# Retrospective — retro-demo" in retro
    assert "Outcome: completed" in retro
    assert "interview, plan, review" in retro  # the phases it completed
    assert "retro-demo:plan" in retro  # the gate that fired
