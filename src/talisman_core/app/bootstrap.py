"""Bootstrap self-improvement run (slice S14.02).

TalisMan's first project is planning its own v1.1. This drives the assembled spiral
(S14.01) through its GATES — interrupt -> approval -> resume — over the real backlog of
v1.1 improvements (the deferred items and risk-register follow-ups accumulated across the
v1 build), and produces the v1.1 backlog artifact. Per ADR-0005 the run is deterministic:
a stub worker behind ``WorkerPort`` and an in-process approver, with no live spend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from talisman_core.app.composition import TalismanApp, build_application
from talisman_core.ports.approval import ApprovalDecision, ApprovalRequest
from talisman_core.ports.worker import WorkerPort, WorkerRequest, WorkerResult
from talisman_core.workflow.spiral import PhaseHandler, SpiralState

PROJECT_ID = "talisman-v1.1"

# The real v1.1 improvement backlog: the deferred items and risk-register follow-ups
# tracked in docs/progress/progress-ledger.md during the v1 build.
V1_1_IMPROVEMENTS: tuple[tuple[str, str], ...] = (
    (
        "worker-subprocess-dedup",
        "Extract shared subprocess plumbing from the Claude/Codex worker adapters.",
    ),
    (
        "eventlog-idempotency-ports",
        "Add EventLog and idempotency ports before their first core consumer.",
    ),
    (
        "agent-family-normalize",
        "Normalize unknown agent names (case/whitespace) in review enforcement.",
    ),
    (
        "budget-toctou",
        "Close the budget check-then-record TOCTOU gap if the gateway becomes concurrent.",
    ),
    (
        "egress-squid-reconcile",
        "Reconcile host- vs domain-granular egress allowlists when wiring the proxy.",
    ),
    ("scoped-credentials", "Design host-side scoped/short-lived credential issuance for workers."),
    ("lessons-retrieval", "Build lessons/retrospective retrieval over the existing SQLite tables."),
    ("live-telegram", "Wire the live Telegram approval bot runtime."),
    ("live-run", "Full live self-improvement run (real workers, gateway, real spend)."),
)

# A self-improvement planning spiral: a tier subset with two human gates.
PLANNING_PHASES: tuple[str, ...] = ("discovery", "synthesis", "plan", "red_team", "slice_approval")
PLANNING_GATES: frozenset[str] = frozenset({"plan", "slice_approval"})


class _StubWorker:
    """Deterministic in-process worker (no subprocess, no spend) for the planning run."""

    def run(self, request: WorkerRequest) -> WorkerResult:
        """Return a deterministic result standing in for a real worker invocation."""
        return WorkerResult(
            worker_name="stub",
            exit_code=0,
            transcript_path=request.prompt_path,
            artifact_paths=(),
            summary=f"planned:{request.slice_id}",
        )


@dataclass
class _RecordingApprover:
    """In-process approver that approves every gate and records the gates it saw."""

    seen: list[str] = field(default_factory=list)

    def request_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        """Record and approve a gate request (the simulated human gate)."""
        self.seen.append(request.gate_id)
        return ApprovalDecision.APPROVE


def planning_handlers(worker: WorkerPort) -> dict[str, PhaseHandler]:
    """Phase handlers that turn the v1.1 improvements into planning artifacts.

    The plan phase routes through the injected ``WorkerPort`` (a deterministic stub here),
    demonstrating that real worker-driven planning plugs into the same seam.
    """

    def discovery(state: SpiralState) -> str:
        return f"discovery:{len(V1_1_IMPROVEMENTS)}-candidates"

    def synthesis(state: SpiralState) -> str:
        return "synthesis:grouped-improvements"

    def plan(state: SpiralState) -> str:
        result = worker.run(
            WorkerRequest(
                project_id=state["project_id"],
                slice_id="v1.1-plan",
                prompt_path=Path("plan.prompt"),
                workspace_path=Path("."),
                timeout_seconds=0,
            )
        )
        return f"plan:{result.summary}"

    def red_team(state: SpiralState) -> str:
        return "red_team:risks-reviewed"

    return {"discovery": discovery, "synthesis": synthesis, "plan": plan, "red_team": red_team}


@dataclass(frozen=True)
class SelfImprovementResult:
    """Outcome of the governed v1.1-planning spiral."""

    final_state: SpiralState
    gates_fired: tuple[str, ...]
    backlog_markdown: str


def render_v1_1_backlog() -> str:
    """Render the v1.1 improvement backlog as markdown — the run's deliverable."""
    lines = [
        "# TalisMan v1.1 improvement backlog",
        "",
        "_Produced by TalisMan's bootstrap self-improvement spiral (slice S14.02)._",
        "",
    ]
    lines.extend(f"- **{key}** — {description}" for key, description in V1_1_IMPROVEMENTS)
    return "\n".join(lines) + "\n"


def run_self_improvement_spiral(app: TalismanApp | None = None) -> SelfImprovementResult:
    """Run TalisMan's v1.1-planning spiral through its gates and return the result."""
    approver = _RecordingApprover()
    application = (
        app
        if app is not None
        else build_application(
            handlers=planning_handlers(_StubWorker()),
            gate_phases=set(PLANNING_GATES),
            log_sink=lambda _line: None,
        )
    )
    final = application.run_gated_project(PROJECT_ID, list(PLANNING_PHASES), approver)
    return SelfImprovementResult(
        final_state=final,
        gates_fired=tuple(approver.seen),
        backlog_markdown=render_v1_1_backlog(),
    )
