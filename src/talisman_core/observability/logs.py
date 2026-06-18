"""Structured JSON logging (slice S12.01).

Emits one JSON object per line so log files are machine-readable and an operator can
diagnose health and events from them. The sink and clock are injected, so the core is
testable without touching the filesystem and timestamps are deterministic under test.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(UTC)


def format_log_line(
    event: str,
    level: str = "info",
    *,
    timestamp: datetime,
    **fields: Any,
) -> str:
    """Format one structured log record as a single JSON line (keys sorted)."""
    record: dict[str, Any] = {
        "timestamp": timestamp.isoformat(),
        "level": level,
        "event": event,
    }
    record.update(fields)
    return json.dumps(record, sort_keys=True)


class StructuredLogger:
    """Write structured JSON log lines to an injected sink (e.g. a file's ``write``)."""

    def __init__(
        self,
        sink: Callable[[str], Any],
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        """Create a logger that writes newline-terminated JSON lines via ``sink``."""
        self._sink = sink
        self._clock = clock

    def log(self, event: str, level: str = "info", **fields: Any) -> None:
        """Emit one structured log record with the current timestamp."""
        line = format_log_line(event, level, timestamp=self._clock(), **fields)
        self._sink(line + "\n")
