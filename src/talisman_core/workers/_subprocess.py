"""Shared worker subprocess plumbing (slice S16.03).

Both vendor worker adapters (Claude Code, Codex CLI) spawn a CLI subprocess the same
way, so that plumbing lives here once. Crucially, this is the single spawn point for
real worker execution, and the default runner ALWAYS builds the child's environment
with long-lived provider/cloud secrets stripped (architecture decision D6): a worker
therefore cannot inherit ``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY`` / ``GITHUB_TOKEN``
etc. from the orchestrator. Keeping the scrub at one unbypassable point — rather than
in each adapter — is what makes the credential-isolation guarantee (AT-13) hold.

Do NOT call ``subprocess.run`` for a worker elsewhere without this scrub.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from talisman_core.security.credentials import worker_environment


@dataclass(frozen=True)
class CommandResult:
    """Outcome of running a worker subprocess: its exit code and captured stdout."""

    exit_code: int
    stdout: str


# A command runner executes a CLI command in a working directory and returns its
# result. Injected into the adapters so their contract is testable without the real CLI.
CommandRunner = Callable[[list[str], Path, int], CommandResult]


def default_runner(args: list[str], cwd: Path, timeout_seconds: int) -> CommandResult:
    """Run a worker command via ``subprocess`` with a credential-scrubbed environment.

    The child receives ``worker_environment()`` — the orchestrator's environment minus
    the long-lived provider/cloud secrets — so the worker never inherits the
    orchestrator's raw keys (D6 / AT-13). Everything else (PATH, HOME, ...) is preserved
    so the worker CLI still runs.
    """
    completed = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
        env=worker_environment(),
    )
    return CommandResult(exit_code=completed.returncode, stdout=completed.stdout)
