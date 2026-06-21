"""Worker credential scrubbing (slice S10.01).

Long-lived provider and cloud credentials must never live inside a worker agent's
environment (architecture decision D6: "if a secret is in the prompt, it is already
gone"). When the orchestrator spawns a worker, it builds the worker's environment
from a base environment with these secrets removed; workers authenticate to their
own providers through their own credentials, not the orchestrator's long-lived keys.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping

# Long-lived secret environment variables stripped from any worker environment,
# matching config.workers.environment_scrub.variables in the architecture package.
DEFAULT_SCRUBBED_VARS: tuple[str, ...] = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "GITHUB_TOKEN",
)


def scrub_environment(
    base_env: Mapping[str, str],
    secret_names: Iterable[str] = DEFAULT_SCRUBBED_VARS,
) -> dict[str, str]:
    """Return a copy of ``base_env`` with the named secret variables removed."""
    removed = set(secret_names)
    return {key: value for key, value in base_env.items() if key not in removed}


def worker_environment(secret_names: Iterable[str] = DEFAULT_SCRUBBED_VARS) -> dict[str, str]:
    """Build a worker subprocess environment from the current process environment,
    with long-lived provider and cloud secrets stripped out.
    """
    return scrub_environment(os.environ, secret_names)


_REDACTED = "[REDACTED]"

# Common secret-shaped tokens, redacted defensively on top of literal env-value redaction.
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),  # OpenAI / Anthropic-style API keys
    re.compile(r"gh[posru]_[A-Za-z0-9]{20,}"),  # GitHub tokens
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key ids
)


def current_secret_values(secret_names: Iterable[str] = DEFAULT_SCRUBBED_VARS) -> tuple[str, ...]:
    """The live values of the scrubbed-secret environment variables, for text redaction."""
    values = [value for name in secret_names if (value := os.environ.get(name))]
    return tuple(values)


def redact_secrets(text: str, *, secret_values: Iterable[str] = ()) -> str:
    """Redact secrets from free text before it is persisted or surfaced.

    Removes (a) any provided literal secret VALUES — e.g. the live values of the scrubbed
    environment variables, via :func:`current_secret_values` — and (b) common secret-shaped
    token patterns. Used wherever raw text (an exception message, a captured log line) might
    carry a credential, e.g. the incident dump (S16.12).
    """
    redacted = text
    for value in secret_values:
        if value:
            redacted = redacted.replace(value, _REDACTED)
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(_REDACTED, redacted)
    return redacted
