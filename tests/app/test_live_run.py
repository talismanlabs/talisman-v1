"""Tests for the live project entrypoint (slice S16.16; ADR-0008).

Driven by an injected fake worker so the full spiral is exercised end to end without launching a
container or spending: we assert each phase's prompt and that one phase's output flows into the
next phase's context.
"""

from __future__ import annotations

from talisman_core.app.live_run import run_live_project
from talisman_core.app.project_run import ProjectSpec
from talisman_core.ports.worker import WorkerRequest, WorkerResult
from talisman_core.workflow.spiral import SPIRAL_PHASES


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
