"""TalisMan service entrypoint (slice S14.01).

``python -m talisman_core.main`` — the entrypoint the systemd unit references. It builds
the assembled application via the composition root and either validates the wiring
(``--dry-run``) or runs a short deterministic demo spiral. Live operation (real workers,
gateway, Telegram) is wired in later slices and at deployment (ADR-0005).
"""

from __future__ import annotations

import argparse
import signal
import time
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType

from talisman_core.app.composition import TalismanApp, build_application
from talisman_core.app.live_entrypoint import LiveRunConfig, run_live

_DEMO_PROJECT_ID = "demo"
_DEMO_PHASES = ("discovery", "plan", "implementation", "review")


class _ServiceRunner:
    """Run the assembled app as a persistent service until stopped by a signal.

    This is what the systemd unit's ExecStart runs: a long-lived process that systemd
    keeps alive and restarts on failure (the entrypoint otherwise runs a demo and exits).
    """

    def __init__(self, app: TalismanApp, heartbeat_seconds: int) -> None:
        """Hold the assembled app and the heartbeat interval."""
        self._app = app
        self._heartbeat = max(1, heartbeat_seconds)
        self._running = True

    def _stop(self, _signum: int, _frame: FrameType | None) -> None:
        self._running = False

    def run(self) -> int:
        """Serve until SIGTERM/SIGINT; return 0 on a clean stop."""
        signal.signal(signal.SIGTERM, self._stop)
        signal.signal(signal.SIGINT, self._stop)
        self._app.logger.log("service_started", mode="serve", heartbeat_seconds=self._heartbeat)
        while self._running:
            self._app.logger.log("heartbeat")
            time.sleep(self._heartbeat)
        self._app.logger.log("service_stopped")
        return 0


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(prog="talisman", description="TalisMan orchestrator.")
    parser.add_argument(
        "--config", default=None, help="Path to config.yaml (reserved for later slices)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and validate the application wiring, then exit.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run as a persistent service (what the systemd unit launches).",
    )
    parser.add_argument(
        "--heartbeat-seconds",
        type=int,
        default=30,
        help="Heartbeat interval for --serve mode.",
    )
    parser.add_argument(
        "--live-project",
        action="store_true",
        help="Run a real project through the spiral on containerized workers "
        "(the supervised live run — real provider calls, real spend).",
    )
    parser.add_argument("--goal", default=None, help="The project goal (with --live-project).")
    parser.add_argument("--project-id", default="live", help="Project id (with --live-project).")
    parser.add_argument(
        "--workspace", default=None, help="Workspace directory (with --live-project)."
    )
    parser.add_argument(
        "--secrets-dir",
        default=None,
        help="Operator secrets directory (default ~/talisman/secrets).",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Durable run-log path (with --live-project). Default: "
        "~/talisman/logs/<project-id>-<timestamp>.log. Tail it to watch the run live.",
    )
    return parser


def _default_log_file(project_id: str, *, now: datetime | None = None) -> Path:
    """The default durable run-log path: ``~/talisman/logs/<project-id>-<UTC timestamp>.log``."""
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    return Path.home() / "talisman" / "logs" / f"{project_id}-{stamp}.log"


def _run_live_project(args: argparse.Namespace) -> int:
    """Assemble and run the supervised live project from the parsed CLI args. Real spend."""
    if not args.goal or not args.workspace:
        raise SystemExit("--live-project requires --goal and --workspace")
    log_file = Path(args.log_file) if args.log_file else _default_log_file(args.project_id)
    config = LiveRunConfig(
        goal=args.goal,
        workspace=Path(args.workspace),
        project_id=args.project_id,
        log_file=log_file,
    )
    if args.secrets_dir:
        config = replace(config, secrets_dir=Path(args.secrets_dir))
    print(f"run log: {log_file}")
    print(f"  watch live: tail -f {log_file}")
    result = run_live(config)
    print(f"live run complete: project={config.project_id} gates_fired={len(result.gates_fired)}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Build and run: a dry-run, a persistent service, a live project, or the demo spiral."""
    args = build_arg_parser().parse_args(argv)
    if args.live_project:
        return _run_live_project(args)
    app = build_application()
    if args.dry_run:
        app.logger.log("dry_run_ok", phases=list(_DEMO_PHASES))
        return 0
    if args.serve:
        return _ServiceRunner(app, args.heartbeat_seconds).run()
    final = app.run_project(_DEMO_PROJECT_ID, list(_DEMO_PHASES))
    app.logger.log("run_complete", completed=final["completed_phases"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
