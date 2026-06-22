"""Live project run: drive the governed spiral on real workers (slice S16.16; ADR-0008).

Wires the phase-prompt policy (S16.15) and the containerized worker (S16.14) into ``run_project``:
for each phase, build the worker instruction from the phase + project goal + prior artifacts,
write it to the workspace, run the worker (inside the no-egress container when it is built by
``build_containerized_worker``), and record the worker's output as the phase artifact that feeds
the next phase.

Running this is the live run — real provider calls, real spend — and is a human-gated step.
Building and unit-testing it (with an injected fake worker) spends nothing.
"""

from __future__ import annotations

from pathlib import Path

from talisman_core.app.project_run import ProjectRunResult, ProjectSpec, run_project
from talisman_core.policies.phase_prompts import build_phase_prompt
from talisman_core.ports.approval import ApprovalPort
from talisman_core.ports.worker import WorkerPort, WorkerRequest
from talisman_core.workflow.spiral import PhaseHandler, SpiralState

# Per-phase worker timeout for a live run (seconds); generous for real agent work.
PHASE_TIMEOUT_SECONDS = 1800


def live_phase_handlers(
    goal: str, worker: WorkerPort, workspace: Path, phases: tuple[str, ...]
) -> dict[str, PhaseHandler]:
    """Worker-driven handlers: each phase prompts ``worker`` and records its output as the artifact.

    The prompt is built from the phase, the goal, and the prior phases' outputs (bounded, fenced as
    untrusted — see ``policies.phase_prompts``); the worker's transcript becomes the phase artifact
    so the next phase builds on it.
    """

    def make_handler(phase: str) -> PhaseHandler:
        def handler(state: SpiralState) -> str:
            prompt = build_phase_prompt(phase, goal, tuple(state["artifacts"]))
            prompt_path = workspace / f"{phase}.prompt.md"
            prompt_path.write_text(prompt, encoding="utf-8")
            result = worker.run(
                WorkerRequest(
                    project_id=state["project_id"],
                    slice_id=phase,
                    prompt_path=prompt_path,
                    workspace_path=workspace,
                    timeout_seconds=PHASE_TIMEOUT_SECONDS,
                )
            )
            return result.transcript_path.read_text(encoding="utf-8")

        return handler

    return {phase: make_handler(phase) for phase in phases}


def run_live_project(
    spec: ProjectSpec,
    *,
    worker: WorkerPort,
    workspace: Path,
    approver: ApprovalPort | None = None,
) -> ProjectRunResult:
    """Run ``spec`` through the governed spiral with each phase driven by ``worker``.

    Each phase's worker runs inside the no-egress container when ``worker`` is built by
    ``build_containerized_worker``; **executing this makes real provider calls** (the human-gated
    live run). Gates fire per ``spec.gate_phases`` and are resolved through ``approver``.
    """
    handlers = live_phase_handlers(spec.goal, worker, workspace, spec.phases)
    return run_project(spec, handlers=handlers, approver=approver)
