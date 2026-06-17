"""Codex CLI worker adapter (slice S07.01).

Wraps the Codex Command Line Interface as a ``WorkerPort``. Vendor-specific
subprocess logic lives in the workers layer; the orchestrator depends only on the
typed port. The command runner is injected so the adapter's contract is testable
without invoking the real CLI.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from talisman_core.ports.worker import WorkerRequest, WorkerResult


@dataclass(frozen=True)
class CommandResult:
    """Outcome of running a worker subprocess: its exit code and captured stdout."""

    exit_code: int
    stdout: str


# A command runner executes a CLI command in a working directory and returns its
# result. Injected so the adapter can be contract-tested without the real CLI.
CommandRunner = Callable[[list[str], Path, int], CommandResult]


def _default_runner(args: list[str], cwd: Path, timeout_seconds: int) -> CommandResult:
    """Run a command via ``subprocess`` and capture its exit code and stdout."""
    completed = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    return CommandResult(exit_code=completed.returncode, stdout=completed.stdout)


class CodexCliWorker:
    """Run Codex CLI as a TalisMan worker (implements the ``WorkerPort`` protocol)."""

    worker_name = "codex_cli"

    def __init__(self, runner: CommandRunner = _default_runner) -> None:
        """Store the injected command runner (defaults to a real subprocess runner)."""
        self._runner = runner

    def run(self, request: WorkerRequest) -> WorkerResult:
        """Run one worker task via the Codex CLI and return a ``WorkerResult``.

        The prompt is read from the request, the CLI is invoked in the request's
        workspace, and the captured transcript is written as an auditable artifact.
        """
        prompt = request.prompt_path.read_text(encoding="utf-8")
        args = ["codex", "exec", prompt]
        result = self._runner(args, request.workspace_path, request.timeout_seconds)
        transcript_path = request.workspace_path / f"{request.slice_id}.transcript.txt"
        transcript_path.write_text(result.stdout, encoding="utf-8")
        return WorkerResult(
            worker_name=self.worker_name,
            exit_code=result.exit_code,
            transcript_path=transcript_path,
            artifact_paths=(transcript_path,),
            summary=(
                f"Codex CLI worker finished slice {request.slice_id} "
                f"with exit code {result.exit_code}."
            ),
        )
