"""Contract and adapter tests for the Codex CLI worker (slice S07.01)."""

from pathlib import Path

from talisman_core.workers._subprocess import CommandResult
from talisman_core.workers.codex_cli import CodexCliWorker


def test_codex_cli_worker_satisfies_worker_contract(worker_request, assert_worker_contract) -> None:
    """The Codex CLI adapter passes the shared WorkerPort contract."""
    worker = CodexCliWorker(runner=lambda args, cwd, timeout, stdin: CommandResult(0, "ran ok"))
    result = assert_worker_contract(worker, worker_request, "codex_cli")
    assert result.exit_code == 0
    assert result.transcript_path.read_text(encoding="utf-8") == "ran ok"


def test_codex_cli_worker_invokes_cli_with_prompt_on_stdin(worker_request) -> None:
    """The adapter runs `codex exec --skip-git-repo-check -` and feeds the prompt on stdin."""
    captured: dict[str, object] = {}

    def fake_runner(args: list[str], cwd: Path, timeout: int, stdin: str | None) -> CommandResult:
        captured["args"] = args
        captured["cwd"] = cwd
        captured["stdin"] = stdin
        return CommandResult(exit_code=0, stdout="done")

    CodexCliWorker(runner=fake_runner).run(worker_request)
    assert captured["args"] == ["codex", "exec", "--skip-git-repo-check", "-"]
    assert captured["stdin"] == "Implement the slice."
    assert captured["cwd"] == worker_request.workspace_path


def test_codex_cli_worker_propagates_nonzero_exit(worker_request) -> None:
    """A failing CLI run is reported faithfully in the WorkerResult exit code."""
    worker = CodexCliWorker(runner=lambda args, cwd, timeout, stdin: CommandResult(2, "boom"))
    result = worker.run(worker_request)
    assert result.exit_code == 2
    assert result.worker_name == "codex_cli"
