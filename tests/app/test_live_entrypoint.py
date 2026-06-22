"""Tests for the live-run entrypoint wiring (slice S16.22).

These prove the assembly — the spec, the keyless worker, and the Telegram approver are built from
config + operator secret files — without launching a container, reaching Telegram, or spending. The
run itself (``run_live`` / ``--live-project``) is the human-gated live step and is not executed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from talisman_core.app.live_entrypoint import (
    DEFAULT_GATE_PHASES,
    LiveRunConfig,
    build_live_approver,
    build_live_spec,
    build_live_worker,
    open_run_log,
)
from talisman_core.workflow.spiral import SPIRAL_PHASES


def _config(tmp_path: Path) -> LiveRunConfig:
    return LiveRunConfig(goal="Build a simple Google News replica", workspace=tmp_path / "ws")


def test_build_live_spec_runs_the_full_spiral_gated_at_the_defaults(tmp_path: Path) -> None:
    """The live spec runs the whole spiral and blocks at the conservative default gate phases."""
    spec = build_live_spec(_config(tmp_path))

    assert spec.phases == SPIRAL_PHASES
    assert spec.gate_phases == DEFAULT_GATE_PHASES
    assert "implementation" in spec.gate_phases  # the irreversible transition is gated
    assert spec.goal == "Build a simple Google News replica"


def test_build_live_worker_builds_the_family_worker(tmp_path: Path) -> None:
    """The worker is the requested family — and (per S16.14/21) containerized + keyless."""
    from talisman_core.workers.claude_code import ClaudeCodeWorker
    from talisman_core.workers.codex_cli import CodexCliWorker

    assert isinstance(build_live_worker(_config(tmp_path)), ClaudeCodeWorker)
    codex_cfg = LiveRunConfig(goal="g", workspace=tmp_path / "w", family="codex")
    assert isinstance(build_live_worker(codex_cfg), CodexCliWorker)


def test_build_live_approver_binds_the_operator_id_as_chat_and_allowlist(tmp_path: Path) -> None:
    """The operator's id (from a secret file) is both the approval chat and the sole allowlist entry."""
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    (secrets / "telegram.token").write_text("123:fake-token", encoding="utf-8")
    (secrets / "telegram.operator_id").write_text("4242\n", encoding="utf-8")

    approver = build_live_approver(secrets)

    assert approver._chat_id == 4242  # type: ignore[attr-defined]
    assert approver._bot._allowlist.is_allowed(4242)  # type: ignore[attr-defined]
    assert not approver._bot._allowlist.is_allowed(9999)  # type: ignore[attr-defined]


def test_live_project_cli_requires_goal_and_workspace() -> None:
    """``--live-project`` without --goal/--workspace exits rather than starting an underspecified run."""
    from talisman_core.main import _run_live_project, build_arg_parser

    args = build_arg_parser().parse_args(["--live-project"])
    with pytest.raises(SystemExit):
        _run_live_project(args)


def test_open_run_log_writes_every_line_to_the_file(tmp_path: Path, capsys) -> None:
    """The run-log sink appends each line to the file (and mirrors it to stdout) for live tailing."""
    log_file = tmp_path / "logs" / "run.log"

    with open_run_log(log_file) as sink:
        sink('{"event": "live_run_started"}\n')
        sink('{"event": "phase_started"}\n')

    body = log_file.read_text(encoding="utf-8")
    assert "live_run_started" in body
    assert "phase_started" in body
    assert "live_run_started" in capsys.readouterr().out  # also mirrored to stdout


def test_open_run_log_without_a_file_is_stdout_only(tmp_path: Path, capsys) -> None:
    """With no log file the sink is stdout-only (cheap default for tests)."""
    with open_run_log(None) as sink:
        sink('{"event": "x"}\n')
    assert '{"event": "x"}' in capsys.readouterr().out


def test_live_run_config_carries_a_log_file(tmp_path: Path) -> None:
    """The config exposes the durable run-log path threaded into the live run."""
    config = LiveRunConfig(goal="g", workspace=tmp_path, log_file=tmp_path / "x.log")
    assert config.log_file == tmp_path / "x.log"
    assert LiveRunConfig(goal="g", workspace=tmp_path).log_file is None  # default off
