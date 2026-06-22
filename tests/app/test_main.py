"""Tests for the TalisMan entrypoint (slice S14.01; --serve runtime S16.10)."""

import signal
from datetime import UTC, datetime
from pathlib import Path

from talisman_core.app.composition import build_application
from talisman_core.main import (
    _default_log_file,
    _run_live_project,
    _ServiceRunner,
    build_arg_parser,
    main,
)


def test_dry_run_returns_zero() -> None:
    """`--dry-run` builds and validates the wiring and exits cleanly."""
    assert main(["--dry-run"]) == 0


def test_demo_run_returns_zero() -> None:
    """A demo spiral runs end-to-end through the assembled app and exits cleanly."""
    assert main([]) == 0


def test_arg_parser_accepts_config_and_dry_run() -> None:
    """The parser accepts the reserved --config path and the --dry-run flag."""
    args = build_arg_parser().parse_args(["--config", "x.yaml", "--dry-run"])
    assert args.config == "x.yaml"
    assert args.dry_run is True


def test_arg_parser_accepts_serve_and_heartbeat() -> None:
    """The parser accepts the --serve flag and the heartbeat interval."""
    args = build_arg_parser().parse_args(["--serve", "--heartbeat-seconds", "5"])
    assert args.serve is True
    assert args.heartbeat_seconds == 5


def test_serve_runs_a_heartbeat_loop_until_a_stop_signal(monkeypatch) -> None:
    """--serve serves until SIGTERM/SIGINT, then exits cleanly (one heartbeat here)."""
    lines: list[str] = []
    app = build_application(log_sink=lines.append)
    runner = _ServiceRunner(app, heartbeat_seconds=1)

    monkeypatch.setattr("talisman_core.main.signal.signal", lambda *_a: None)
    # Make the first sleep request the stop, so the loop runs exactly one heartbeat.
    monkeypatch.setattr(
        "talisman_core.main.time.sleep",
        lambda _s: runner._stop(signal.SIGTERM, None),
    )

    assert runner.run() == 0
    joined = " ".join(lines)
    assert "service_started" in joined
    assert "heartbeat" in joined
    assert "service_stopped" in joined


def test_main_serve_dispatches_to_the_service_runner(monkeypatch) -> None:
    """`main(['--serve'])` routes to the persistent service runner."""
    called = {"ran": False}

    def stub_run(_self: _ServiceRunner) -> int:
        called["ran"] = True
        return 0

    monkeypatch.setattr("talisman_core.main._ServiceRunner.run", stub_run)
    assert main(["--serve"]) == 0
    assert called["ran"] is True


def test_default_log_file_is_a_timestamped_path_under_talisman_logs() -> None:
    """The default run-log path is ~/talisman/logs/<project>-<UTC timestamp>.log."""
    path = _default_log_file("news", now=datetime(2026, 6, 22, 14, 5, 9, tzinfo=UTC))
    assert path == Path.home() / "talisman" / "logs" / "news-20260622T140509Z.log"


def test_arg_parser_accepts_log_file() -> None:
    """The parser accepts an explicit --log-file path for a live run."""
    args = build_arg_parser().parse_args(["--live-project", "--log-file", "/tmp/run.log"])
    assert args.log_file == "/tmp/run.log"


def test_run_live_project_threads_a_log_file_into_the_config(monkeypatch, capsys) -> None:
    """_run_live_project derives a default log file, prints it, and passes it to run_live."""
    captured = {}

    def fake_run_live(config):
        captured["config"] = config

        class _Result:
            gates_fired = ()

        return _Result()

    monkeypatch.setattr("talisman_core.main.run_live", fake_run_live)
    args = build_arg_parser().parse_args(
        ["--live-project", "--goal", "g", "--workspace", "/tmp/ws", "--project-id", "news"]
    )

    assert _run_live_project(args) == 0
    config = captured["config"]
    assert config.log_file is not None
    assert config.log_file.parent == Path.home() / "talisman" / "logs"
    assert config.log_file.name.startswith("news-")
    out = capsys.readouterr().out
    assert "watch live: tail -f" in out  # the operator is told where to watch
