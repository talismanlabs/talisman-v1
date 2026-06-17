"""Worker credential scrubbing (slice S10.01).

Long-lived provider and cloud credentials must never live inside a worker agent's
environment (architecture decision D6: "if a secret is in the prompt, it is already
gone"). When the orchestrator spawns a worker, it builds the worker's environment
from a base environment with these secrets removed; workers authenticate to their
own providers through their own credentials, not the orchestrator's long-lived keys.
"""

from __future__ import annotations

import os
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
