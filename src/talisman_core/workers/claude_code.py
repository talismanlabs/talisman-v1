"""Claude Code worker adapter (slice S06.01; shared scrubbing runner wired in S16.03).

Wraps the Claude Code Command Line Interface as a ``WorkerPort``. Vendor-specific
subprocess logic lives in the workers layer; the orchestrator depends only on the
typed port. The command runner is injected so the adapter's contract is testable
without invoking the real CLI (which would spend tokens and require network access).
The default runner is the shared, credential-scrubbing ``default_runner`` so a worker
never inherits the orchestrator's long-lived provider keys (D6 / AT-13).
"""

from __future__ import annotations

from talisman_core.ports.worker import WorkerRequest, WorkerResult
from talisman_core.workers._subprocess import CommandRunner, default_runner


class ClaudeCodeWorker:
    """Run Claude Code as a TalisMan worker (implements the ``WorkerPort`` protocol)."""

    worker_name = "claude_code"

    def __init__(self, runner: CommandRunner = default_runner) -> None:
        """Store the injected command runner (defaults to the scrubbing subprocess runner)."""
        self._runner = runner

    def run(self, request: WorkerRequest) -> WorkerResult:
        """Run one worker task via the Claude Code CLI and return a ``WorkerResult``.

        The prompt is read from the request, the CLI is invoked in the request's
        workspace, and the captured transcript is written as an auditable artifact.
        """
        prompt = request.prompt_path.read_text(encoding="utf-8")
        args = ["claude", "-p", prompt]
        result = self._runner(args, request.workspace_path, request.timeout_seconds, None)
        transcript_path = request.workspace_path / f"{request.slice_id}.transcript.txt"
        transcript_path.write_text(result.stdout, encoding="utf-8")
        return WorkerResult(
            worker_name=self.worker_name,
            exit_code=result.exit_code,
            transcript_path=transcript_path,
            artifact_paths=(transcript_path,),
            summary=(
                f"Claude Code worker finished slice {request.slice_id} "
                f"with exit code {result.exit_code}."
            ),
        )
