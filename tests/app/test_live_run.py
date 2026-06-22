"""Tests for the live project entrypoint (slice S16.16; ADR-0008).

Driven by an injected fake worker so the full spiral is exercised end to end without launching a
container or spending: we assert each phase's prompt and that one phase's output flows into the
next phase's context.
"""

from __future__ import annotations

import json

from talisman_core.app.live_run import live_phase_handlers, run_live_project
from talisman_core.app.project_run import ProjectSpec
from talisman_core.observability.logs import StructuredLogger
from talisman_core.ports.worker import WorkerRequest, WorkerResult
from talisman_core.workflow.spiral import SPIRAL_PHASES, SpiralState


class _RecordingWorker:
    """A fake worker that records each phase's prompt and writes a deterministic transcript."""

    def __init__(self) -> None:
        self.prompts: dict[str, str] = {}

    def run(self, request: WorkerRequest) -> WorkerResult:
        self.prompts[request.slice_id] = request.prompt_path.read_text(encoding="utf-8")
        transcript = request.workspace_path / f"{request.slice_id}.transcript.txt"
        transcript.write_text(f"OUTPUT[{request.slice_id}]", encoding="utf-8")
        return WorkerResult(
            worker_name="fake",
            exit_code=0,
            transcript_path=transcript,
            artifact_paths=(transcript,),
            summary=f"did {request.slice_id}",
        )


def _spec() -> ProjectSpec:
    return ProjectSpec(
        project_id="news-replica",
        phases=SPIRAL_PHASES,
        gate_phases=frozenset(),  # no gates: exercise the handler wiring without interrupts
        goal="build a simple Google News replica",
    )


def test_live_run_drives_every_phase_through_the_worker(tmp_path) -> None:
    """The full spiral runs, each phase prompting the worker with the phase + goal."""
    worker = _RecordingWorker()

    result = run_live_project(_spec(), worker=worker, workspace=tmp_path)

    assert result.final_state["completed_phases"] == list(SPIRAL_PHASES)
    assert set(worker.prompts) == set(SPIRAL_PHASES)  # every phase prompted the worker
    assert "phase: interview" in worker.prompts["interview"]
    assert "Google News replica" in worker.prompts["discovery"]  # the goal is carried


def test_prior_phase_output_flows_into_the_next_phase(tmp_path) -> None:
    """A phase's worker output becomes fenced context in a later phase's prompt (ADR-0008)."""
    worker = _RecordingWorker()

    run_live_project(_spec(), worker=worker, workspace=tmp_path)

    # discovery's prompt carries interview's output as untrusted prior context
    assert "OUTPUT[interview]" in worker.prompts["discovery"]
    assert "UNTRUSTED" in worker.prompts["discovery"]


def test_implementation_prompt_keeps_the_branch_only_constraint(tmp_path) -> None:
    """Even mid-run, the implementation phase still forbids push/merge (ADR-0008 C)."""
    worker = _RecordingWorker()

    run_live_project(_spec(), worker=worker, workspace=tmp_path)

    impl = worker.prompts["implementation"]
    assert "never push to main" in impl
    assert "never merge" in impl


def _initial_state(project_id: str) -> SpiralState:
    return {
        "project_id": project_id,
        "tier": "standard",
        "phase_sequence": [],
        "current_phase": "",
        "completed_phases": [],
        "pending_gate_id": None,
        "last_decision": None,
        "artifacts": [],
        "escalations_today": 0,
    }


def test_phase_handler_logs_started_and_completed_progress(tmp_path) -> None:
    """With a logger injected, a phase emits started + completed events with duration and size."""
    lines: list[str] = []
    logger = StructuredLogger(lines.append)
    ticks = iter([10.0, 14.5])  # start, end → duration 4.5s (deterministic clock)
    handlers = live_phase_handlers(
        "build a simple Google News replica",
        _RecordingWorker(),
        tmp_path,
        SPIRAL_PHASES,
        logger=logger,
        clock=lambda: next(ticks),
    )

    output = handlers["discovery"](_initial_state("news-replica"))

    events = [json.loads(line) for line in lines]
    started = next(e for e in events if e["event"] == "phase_started")
    completed = next(e for e in events if e["event"] == "phase_completed")
    assert started["phase"] == "discovery"
    assert completed["phase"] == "discovery"
    assert completed["duration_seconds"] == 4.5
    assert completed["output_chars"] == len(output)  # "OUTPUT[discovery]"
    assert completed["project_id"] == "news-replica"


def test_phase_handlers_stay_silent_without_a_logger(tmp_path) -> None:
    """No logger → no progress events (the deterministic test path is unchanged)."""
    handlers = live_phase_handlers("g", _RecordingWorker(), tmp_path, SPIRAL_PHASES)
    # Runs without raising and produces the artifact, emitting nothing.
    assert handlers["interview"](_initial_state("p")) == "OUTPUT[interview]"
