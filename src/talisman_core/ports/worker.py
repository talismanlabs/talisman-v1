"""Worker execution port for external coding and reasoning agents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class WorkerRequest:
    """Structured request sent to an external coding or reasoning worker."""

    project_id: str
    slice_id: str
    prompt_path: Path
    workspace_path: Path
    timeout_seconds: int


@dataclass(frozen=True)
class WorkerResult:
    """Structured result returned by a worker adapter.

    The orchestrator stores results as artifacts. It must not blindly execute
    worker-generated commands without going through the approval and review
    gates required by policy.
    """

    worker_name: str
    exit_code: int
    transcript_path: Path
    artifact_paths: tuple[Path, ...]
    summary: str


class WorkerPort(Protocol):
    """Interface implemented by Claude Code, Codex CLI, and future workers."""

    def run(self, request: WorkerRequest) -> WorkerResult:
        """Run one worker task and return a structured, auditable result."""
        ...
