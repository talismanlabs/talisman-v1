"""Codex CLI worker adapter (slice S07.01; shared scrubbing runner wired in S16.03).

Wraps the Codex Command Line Interface as a ``WorkerPort``. Vendor-specific subprocess
logic lives in the workers layer; the orchestrator depends only on the typed port. The
command runner is injected so the adapter's contract is testable without invoking the
real CLI. The default runner is the shared, credential-scrubbing ``default_runner`` so a
worker never inherits the orchestrator's long-lived provider keys (D6 / AT-13).
"""

from __future__ import annotations

from talisman_core.ports.worker import WorkerRequest, WorkerResult
from talisman_core.workers._subprocess import CommandRunner, default_runner


class CodexCliWorker:
    """Run Codex CLI as a TalisMan worker (implements the ``WorkerPort`` protocol)."""

    worker_name = "codex_cli"

    def __init__(self, runner: CommandRunner = default_runner) -> None:
        """Store the injected command runner (defaults to the scrubbing subprocess runner)."""
        self._runner = runner

    def run(self, request: WorkerRequest) -> WorkerResult:
        """Run one worker task via the Codex CLI and return a ``WorkerResult``.

        The prompt is read from the request, the CLI is invoked in the request's
        workspace, and the captured transcript is written as an auditable artifact.
        """
        prompt = request.prompt_path.read_text(encoding="utf-8")
        # Pass the prompt on stdin (the ``-`` argument) instead of argv so it stays out of
        # ps / /proc, and skip the git-repo check so the CLI runs in any workspace (S16.05,
        # AT-08; the invocation Codex CLI actually requires).
        args = ["codex", "exec", "--skip-git-repo-check", "-"]
        result = self._runner(args, request.workspace_path, request.timeout_seconds, prompt)
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
