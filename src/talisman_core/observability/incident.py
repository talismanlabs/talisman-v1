"""Incident dump on catastrophic halt (slice S16.12, AT-19).

When a project run halts catastrophically — an unhandled error escaping the governed
spiral — an unattended operator needs something to diagnose with. This writes a structured
markdown incident dump (what was running, why it halted, and the recent log lines) to a
durable directory, automatically, before the error propagates.

Secrets are redacted at this write point (the unbypassable seam): the reason and every log
line pass through :func:`redact_secrets`, which strips the live values of the scrubbed
environment variables plus common secret-shaped tokens, so a credential that leaked into an
exception message or a log field is never persisted to disk. The filename is derived from a
filesystem-safe slug (never the raw project id) so a project id containing path separators
cannot escape the dump directory.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from talisman_core.security.credentials import current_secret_values, redact_secrets

_MAX_LOG_LINES = 50


def _safe_slug(project_id: str) -> str:
    """A filesystem-safe slug for a project id: no path separators, no traversal, bounded."""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", project_id).strip("._-")
    return slug[:64] or "project"


def write_incident_dump(
    directory: Path,
    *,
    project_id: str,
    phases: tuple[str, ...],
    reason: str,
    logs: list[str],
) -> Path:
    """Write a redacted, timestamped markdown incident dump and return its path.

    ``directory`` is created if missing. The reason and recent log lines are redacted of
    secrets before writing. The filename uses a filesystem-safe slug plus a timestamp and a
    short random suffix, so successive incidents never overwrite one another and a malicious
    or generic project id cannot traverse outside ``directory``.
    """
    directory.mkdir(parents=True, exist_ok=True)
    now = datetime.now(tz=UTC)
    secret_values = current_secret_values()

    safe_reason = redact_secrets(reason, secret_values=secret_values)
    recent = [redact_secrets(line, secret_values=secret_values) for line in logs[-_MAX_LOG_LINES:]]

    name = f"incident-{_safe_slug(project_id)}-{now.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}.md"
    path = directory / name

    lines = [
        f"# Incident dump — {project_id}",
        "",
        f"- Time (UTC): {now.isoformat()}",
        f"- Reason: {safe_reason}",
        f"- Phases: {', '.join(phases) if phases else '(none)'}",
        "",
        "## Recent log lines",
    ]
    if recent:
        lines.extend(f"- {line}" for line in recent)
    else:
        lines.append("- (none captured)")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
