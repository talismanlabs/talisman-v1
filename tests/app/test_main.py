"""Tests for the TalisMan entrypoint (slice S14.01)."""

from talisman_core.main import build_arg_parser, main


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
