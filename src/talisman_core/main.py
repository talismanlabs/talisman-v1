"""TalisMan service entrypoint (slice S14.01).

``python -m talisman_core.main`` — the entrypoint the systemd unit references. It builds
the assembled application via the composition root and either validates the wiring
(``--dry-run``) or runs a short deterministic demo spiral. Live operation (real workers,
gateway, Telegram) is wired in later slices and at deployment (ADR-0005).
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from talisman_core.app.composition import build_application

_DEMO_PROJECT_ID = "demo"
_DEMO_PHASES = ("discovery", "plan", "implementation", "review")


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Build the application and run either a dry-run validation or a demo spiral."""
    args = build_arg_parser().parse_args(argv)
    app = build_application()
    if args.dry_run:
        app.logger.log("dry_run_ok", phases=list(_DEMO_PHASES))
        return 0
    final = app.run_project(_DEMO_PROJECT_ID, list(_DEMO_PHASES))
    app.logger.log("run_complete", completed=final["completed_phases"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
