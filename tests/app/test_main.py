"""Tests for the TalisMan entrypoint (slice S14.01; --serve runtime S16.10)."""

import signal

from talisman_core.app.composition import build_application
from talisman_core.main import _ServiceRunner, build_arg_parser, main


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
