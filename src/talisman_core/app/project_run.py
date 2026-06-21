"""Generic project intake (slice S16.09).

The governed spiral is project-agnostic: ``composition.run_gated_project`` runs ANY project
id through a chosen phase sequence with chosen gates. This packages that into a
``ProjectSpec`` + ``run_project`` entry point, so TalisMan can be pointed at a brand-new
project — not just its own bootstrap (S14.02) — and a test proves a greenfield project runs
end to end through the same governed gates.

Workers stay deterministic here (the composition defaults), so a new project is exercised
with no live worker, gateway, or spend. Swapping in real, containerized workers (inject
``handlers`` that route a phase through a ``WorkerPort`` backed by the container runner) is
the live run, which remains a human-authorized step.
"""

from __future__ import annotations

import contextlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from talisman_core.app.composition import TalismanApp, build_application
from talisman_core.observability.incident import write_incident_dump
from talisman_core.ports.approval import ApprovalDecision, ApprovalPort, ApprovalRequest
from talisman_core.ports.memory import Lesson, LessonQuery, MemoryPort
from talisman_core.workflow.spiral import PhaseHandler, SpiralState

_DEFAULT_INCIDENT_DIR = Path.home() / "talisman" / "incidents"


@dataclass(frozen=True)
class ProjectSpec:
    """A project to run through the governed spiral: its id, phase sequence, and gate phases."""

    project_id: str
    phases: tuple[str, ...]
    gate_phases: frozenset[str] = frozenset()
    tier: str = "standard"
    domain_tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectRunResult:
    """Outcome of running a project spec through the governed spiral."""

    final_state: SpiralState
    gates_fired: tuple[str, ...]
    retrospective: str
    surfaced_lessons: tuple[Lesson, ...]


@dataclass
class _ApproveAllApprover:
    """In-process approver that approves every gate and records the gates it saw."""

    seen: list[str] = field(default_factory=list)

    def request_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        """Record and approve a gate request (the simulated human gate)."""
        self.seen.append(request.gate_id)
        return ApprovalDecision.APPROVE


def generate_retrospective(
    spec: ProjectSpec, final_state: SpiralState, gates_fired: tuple[str, ...]
) -> str:
    """Render a markdown retrospective for a completed project run (AT-16).

    Produced automatically at project close: a concise record of what ran — phases
    completed, gates that fired, artifacts produced, and whether every phase in the spec
    was reached — so each run leaves a durable, reviewable trace.
    """
    completed = final_state["completed_phases"]
    artifacts = final_state["artifacts"]
    outcome = "completed" if set(spec.phases) <= set(completed) else "incomplete"
    lines = [
        f"# Retrospective — {spec.project_id}",
        "",
        f"- Outcome: {outcome}",
        f"- Tier: {spec.tier}",
        f"- Phases completed: {', '.join(completed) if completed else '(none)'}",
        f"- Gates fired: {', '.join(gates_fired) if gates_fired else '(none)'}",
        f"- Artifacts produced: {len(artifacts)}",
    ]
    return "\n".join(lines) + "\n"


def _surface_lessons_at_intake(
    spec: ProjectSpec, memory: MemoryPort | None, application: TalismanApp
) -> tuple[Lesson, ...]:
    """Retrieve active lessons relevant to the spec and surface them at intake (AT-17)."""
    if memory is None:
        return ()
    lessons = memory.retrieve_lessons(LessonQuery(domain_tags=spec.domain_tags))
    application.logger.log(
        "lessons_surfaced",
        project_id=spec.project_id,
        count=len(lessons),
        lesson_ids=[lesson.lesson_id for lesson in lessons],
    )
    return lessons


def run_project(
    spec: ProjectSpec,
    *,
    handlers: Mapping[str, PhaseHandler] | None = None,
    app: TalismanApp | None = None,
    approver: ApprovalPort | None = None,
    incident_dir: Path | None = None,
    memory: MemoryPort | None = None,
) -> ProjectRunResult:
    """Run ``spec`` through the governed spiral and return its final state + gates fired.

    With no overrides the run is deterministic (composition defaults + auto-approval), so a
    new project can be exercised end to end with no live worker, gateway, or spend. Inject
    ``handlers`` to drive phases through real workers, or ``approver`` to gate through a real
    approval channel.

    If ``memory`` is supplied, the active lessons relevant to the spec's ``domain_tags`` are
    retrieved and surfaced at intake (logged, and returned on the result) so accumulated
    lessons inform each new project (AT-17).

    If the run halts catastrophically (an unhandled error escapes the spiral), an incident
    dump of the reason + recent logs is written to ``incident_dir`` (default
    ``~/talisman/incidents``) before the error re-raises (AT-19).
    """
    resolved_approver: ApprovalPort = approver if approver is not None else _ApproveAllApprover()
    captured_logs: list[str] = []
    application = app or build_application(
        handlers=handlers,
        gate_phases=set(spec.gate_phases),
        log_sink=captured_logs.append,
    )
    surfaced_lessons = _surface_lessons_at_intake(spec, memory, application)
    try:
        final = application.run_gated_project(
            spec.project_id, list(spec.phases), resolved_approver, tier=spec.tier
        )
    except Exception as exc:
        target = incident_dir if incident_dir is not None else _DEFAULT_INCIDENT_DIR
        # Best-effort: a dump failure must never mask the original catastrophic error.
        with contextlib.suppress(Exception):
            write_incident_dump(
                target,
                project_id=spec.project_id,
                phases=spec.phases,
                reason=repr(exc),
                logs=captured_logs,
            )
        raise
    gates_fired = tuple(getattr(resolved_approver, "seen", ()))
    retrospective = generate_retrospective(spec, final, gates_fired)
    return ProjectRunResult(
        final_state=final,
        gates_fired=gates_fired,
        retrospective=retrospective,
        surfaced_lessons=surfaced_lessons,
    )
