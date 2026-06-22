"""Tests for the generic project intake (slice S16.09).

These prove project-agnosticism: a brand-new project — not TalisMan's own bootstrap — runs
end to end through the governed spiral, with its own phases and gates, deterministically.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from talisman_core.adapters.sqlite.memory import SQLiteMemoryStore
from talisman_core.app.project_run import ProjectRunResult, ProjectSpec, run_project
from talisman_core.ports.approval import ApprovalDecision, ApprovalRequest
from talisman_core.ports.memory import Lesson, LessonSeverity, LessonStatus


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


def test_a_catastrophic_halt_writes_an_incident_dump(tmp_path) -> None:
    """An unhandled error during a run writes an incident dump, then propagates (AT-19)."""

    def boom(_state: object) -> str:
        raise RuntimeError("planner exploded")

    spec = ProjectSpec("doomed", ("plan",))

    with pytest.raises(RuntimeError, match="planner exploded"):
        run_project(spec, handlers={"plan": boom}, incident_dir=tmp_path)

    dumps = list(tmp_path.glob("incident-doomed-*.md"))
    assert len(dumps) == 1
    body = dumps[0].read_text(encoding="utf-8")
    assert "# Incident dump — doomed" in body
    assert "planner exploded" in body  # the reason
    assert "Phases: plan" in body


def test_incident_dump_redacts_secrets(tmp_path, monkeypatch) -> None:
    """Secrets that leak into the error/logs are redacted from the dump (AT-19, security)."""
    env_secret = "not-a-real-secret-just-a-test-value"  # redacted via the live env-var value
    monkeypatch.setenv("OPENAI_API_KEY", env_secret)
    token = "sk-DEMOabcdefghij1234567890"  # redacted via the secret-shaped pattern

    def boom(_state: object) -> str:
        raise RuntimeError(f"auth failed: env={env_secret} token={token}")

    spec = ProjectSpec("leaky", ("plan",))
    with pytest.raises(RuntimeError):
        run_project(spec, handlers={"plan": boom}, incident_dir=tmp_path)

    body = next(tmp_path.glob("incident-leaky-*.md")).read_text(encoding="utf-8")
    assert env_secret not in body  # redacted via the live env-var value
    assert token not in body  # redacted via the secret-shaped pattern
    assert "[REDACTED]" in body


def test_incident_dump_filename_is_path_safe(tmp_path) -> None:
    """A project id with path separators cannot traverse outside the dump directory (AT-19)."""

    def boom(_state: object) -> str:
        raise RuntimeError("boom")

    spec = ProjectSpec("../../etc/evil", ("plan",))
    with pytest.raises(RuntimeError):
        run_project(spec, handlers={"plan": boom}, incident_dir=tmp_path)

    dumps = list(tmp_path.glob("incident-*.md"))
    assert len(dumps) == 1
    assert dumps[0].parent == tmp_path  # written inside the dir, not traversed out
    assert "../../etc/evil" in dumps[0].read_text(encoding="utf-8")  # real id kept in the body


def test_repeated_incidents_do_not_overwrite(tmp_path) -> None:
    """Successive incidents for the same project get distinct files (AT-19)."""

    def boom(_state: object) -> str:
        raise RuntimeError("boom")

    spec = ProjectSpec("dup", ("plan",))
    for _ in range(2):
        with pytest.raises(RuntimeError):
            run_project(spec, handlers={"plan": boom}, incident_dir=tmp_path)

    assert len(list(tmp_path.glob("incident-dup-*.md"))) == 2


def test_relevant_lessons_are_surfaced_at_intake(tmp_path) -> None:
    """run_project retrieves active lessons relevant to the spec and surfaces them at intake (AT-17)."""
    store = SQLiteMemoryStore(tmp_path / "state.sqlite3")
    store.record_lesson(
        Lesson(
            lesson_id="L-ci",
            project_id="past-project",
            domain_tags=("ci",),
            severity=LessonSeverity.HIGH,
            statement="pin the CI actions",
            detail_ref=Path("docs/lessons/L-ci.md"),
            status=LessonStatus.ACTIVE,
            lesson_date=date(2026, 6, 1),
        )
    )

    spec = ProjectSpec("new-project", ("plan",), domain_tags=("ci",))
    result = run_project(spec, memory=store)

    assert [lesson.lesson_id for lesson in result.surfaced_lessons] == ["L-ci"]
    assert result.final_state["completed_phases"] == ["plan"]  # the run still completes


def test_no_memory_surfaces_no_lessons() -> None:
    """Without a memory store the default path is unchanged: no lessons surfaced."""
    result = run_project(ProjectSpec("plain", ("plan",)))
    assert result.surfaced_lessons == ()


def test_log_sink_observes_the_run_lifecycle() -> None:
    """An injected log_sink receives the structured lifecycle events — the run isn't a black box."""
    lines: list[str] = []
    spec = ProjectSpec("observed", ("interview", "plan", "review"), frozenset({"plan"}))

    run_project(spec, log_sink=lines.append)

    joined = " ".join(lines)
    assert "gated_project_started" in joined
    assert "gated_project_finished" in joined
    assert "observed" in joined  # the project id is carried on the events


def test_log_sink_does_not_disable_the_incident_dump(tmp_path) -> None:
    """Teeing to a log_sink still keeps the in-memory buffer used for the incident dump (AT-19)."""

    def boom(_state: object) -> str:
        raise RuntimeError("planner exploded")

    lines: list[str] = []
    spec = ProjectSpec("doomed-but-logged", ("plan",))

    with pytest.raises(RuntimeError, match="planner exploded"):
        run_project(spec, handlers={"plan": boom}, incident_dir=tmp_path, log_sink=lines.append)

    # the external sink saw the run start...
    assert any("gated_project_started" in line for line in lines)
    # ...and the incident dump was still written from the retained buffer
    assert len(list(tmp_path.glob("incident-doomed-but-logged-*.md"))) == 1
