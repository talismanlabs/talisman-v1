"""Contract and adapter tests for the Claude Code worker (slice S06.01)."""

from pathlib import Path

from talisman_core.workers._subprocess import CommandResult
from talisman_core.workers.claude_code import ClaudeCodeWorker


def test_claude_code_worker_satisfies_worker_contract(
    worker_request, assert_worker_contract
) -> None:
    """The Claude Code adapter passes the shared WorkerPort contract."""
    worker = ClaudeCodeWorker(runner=lambda args, cwd, timeout, stdin: CommandResult(0, "ran ok"))
    result = assert_worker_contract(worker, worker_request, "claude_code")
    assert result.exit_code == 0
    assert result.transcript_path.read_text(encoding="utf-8") == "ran ok"


def test_claude_code_worker_invokes_cli_in_workspace(worker_request) -> None:
    """The adapter builds a `claude -p <prompt>` command and runs it in the workspace."""
    captured: dict[str, object] = {}

    def fake_runner(args: list[str], cwd: Path, timeout: int, stdin: str | None) -> CommandResult:
        captured["args"] = args
        captured["cwd"] = cwd
        captured["stdin"] = stdin
        return CommandResult(exit_code=0, stdout="done")

    ClaudeCodeWorker(runner=fake_runner).run(worker_request)
    assert captured["args"] == ["claude", "-p", "Implement the slice."]
    assert captured["cwd"] == worker_request.workspace_path
    assert captured["stdin"] is None  # Claude takes the prompt on argv, not stdin


def test_claude_code_worker_propagates_nonzero_exit(worker_request) -> None:
    """A failing CLI run is reported faithfully in the WorkerResult exit code."""
    worker = ClaudeCodeWorker(runner=lambda args, cwd, timeout, stdin: CommandResult(2, "boom"))
    result = worker.run(worker_request)
    assert result.exit_code == 2
    assert result.worker_name == "claude_code"
