"""Shared fixtures for worker-adapter contract tests.

The ``assert_worker_contract`` fixture defines the behavior every ``WorkerPort``
implementation must satisfy, so the Claude Code worker (S06.01) and the Codex CLI
worker (S07.01) are held to the same contract.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from talisman_core.ports.worker import WorkerPort, WorkerRequest, WorkerResult


@pytest.fixture
def worker_request(tmp_path: Path) -> WorkerRequest:
    """A WorkerRequest backed by a real prompt file and workspace under tmp_path."""
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("Implement the slice.", encoding="utf-8")
    workspace_path = tmp_path / "workspace"
    workspace_path.mkdir()
    return WorkerRequest(
        project_id="p1",
        slice_id="S00.01",
        prompt_path=prompt_path,
        workspace_path=workspace_path,
        timeout_seconds=60,
    )


WorkerContractAssertion = Callable[[WorkerPort, WorkerRequest, str], WorkerResult]


@pytest.fixture
def assert_worker_contract() -> WorkerContractAssertion:
    """Return the assertion that any WorkerPort implementation must satisfy."""

    def _assert(worker: WorkerPort, request: WorkerRequest, expected_name: str) -> WorkerResult:
        result = worker.run(request)
        assert isinstance(result, WorkerResult)
        assert result.worker_name == expected_name
        assert result.transcript_path.exists()
        assert result.transcript_path in result.artifact_paths
        assert result.summary
        return result

    return _assert
