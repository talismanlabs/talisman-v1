"""Tests for the shared worker subprocess runner (slice S16.03).

The default runner is the single, unbypassable spawn point for real worker execution,
and it must strip the orchestrator's long-lived provider/cloud secrets from the child
process environment (architecture decision D6 / acceptance test AT-13). These tests
spawn a REAL child process, so they prove the wiring end-to-end rather than mocking it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from talisman_core.security.credentials import DEFAULT_SCRUBBED_VARS
from talisman_core.workers._subprocess import default_runner


def test_default_runner_strips_secrets_from_a_real_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real child spawned by the default runner cannot see the long-lived
    provider/cloud secrets present in the orchestrator's environment (AT-13)."""
    for var in DEFAULT_SCRUBBED_VARS:
        monkeypatch.setenv(var, "PLANTED-SECRET-VALUE")
    names = list(DEFAULT_SCRUBBED_VARS)
    code = f"import os; print(','.join(v for v in {names!r} if v in os.environ))"

    result = default_runner([sys.executable, "-c", code], tmp_path, 30)

    assert result.exit_code == 0
    leaked = result.stdout.strip()
    assert leaked == "", f"worker child inherited scrubbed secrets: {leaked}"


def test_default_runner_preserves_non_secret_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scrub removes only the named secrets, leaving the rest of the environment
    (e.g. PATH and other variables) intact so the worker CLI still runs."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "PLANTED")
    monkeypatch.setenv("TALISMAN_NONSECRET", "keep-me")
    code = (
        "import os; "
        "print(os.environ.get('TALISMAN_NONSECRET', 'MISSING'), "
        "'ANTHROPIC_API_KEY' in os.environ)"
    )

    result = default_runner([sys.executable, "-c", code], tmp_path, 30)

    assert result.exit_code == 0
    assert result.stdout.strip() == "keep-me False"


def test_default_runner_passes_stdin_to_the_child(tmp_path: Path) -> None:
    """``stdin_text`` is delivered to the child process's standard input (S16.05) — this is
    how a worker prompt is passed off the command line (out of ps / /proc)."""
    code = "import sys; sys.stdout.write(sys.stdin.read().upper())"

    result = default_runner([sys.executable, "-c", code], tmp_path, 30, "prompt via stdin")

    assert result.exit_code == 0
    assert result.stdout == "PROMPT VIA STDIN"
