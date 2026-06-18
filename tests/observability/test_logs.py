"""Tests for structured JSON logging (slice S12.01)."""

import json
from datetime import UTC, datetime

from talisman_core.observability.logs import StructuredLogger, format_log_line


def test_format_log_line_is_valid_json_with_core_fields() -> None:
    """A formatted record is one JSON object carrying timestamp, level, event, and fields."""
    timestamp = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    line = format_log_line("slice_started", "info", timestamp=timestamp, slice_id="S12.01")
    record = json.loads(line)
    assert record["event"] == "slice_started"
    assert record["level"] == "info"
    assert record["timestamp"] == "2026-06-18T12:00:00+00:00"
    assert record["slice_id"] == "S12.01"


def test_logger_writes_one_json_line_per_event() -> None:
    """The logger writes a newline-terminated JSON line to its sink, using the injected clock."""
    lines: list[str] = []
    fixed = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    logger = StructuredLogger(lines.append, clock=lambda: fixed)

    logger.log("gateway_call", status="ok", cost_usd=0.01)
    logger.log("budget_paused", level="warning", cap="daily")

    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["event"] == "gateway_call"
    assert first["status"] == "ok"
    assert lines[0].endswith("\n")
    second = json.loads(lines[1])
    assert second["level"] == "warning"
    assert second["event"] == "budget_paused"
