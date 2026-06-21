"""Live-execution wiring: real containerized workers for the governed spiral (slice S16.14).

Assembles the orchestrator's real-run path: the worker adapters (Claude Code / Codex) whose
commands execute inside the ``--internal``-network containers from S16.06 / ADR-0007, so a
real project is worked by real agents that physically cannot egress except through the proxy
(the AT-14 boundary). The worker adapters are unchanged; only their command runner becomes the
``ContainerRunner``, so every command a worker issues is wrapped in the isolating ``podman run``.

Building this wiring spends nothing and runs no container; only *running* it — the supervised
live run, a human-gated step on the deploy box — makes real provider calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from talisman_core.ports.worker import WorkerPort
from talisman_core.workers._container import ContainerRunner
from talisman_core.workers._subprocess import CommandRunner, default_runner
from talisman_core.workers.claude_code import ClaudeCodeWorker
from talisman_core.workers.codex_cli import CodexCliWorker

WorkerFamily = Literal["claude", "codex"]


@dataclass(frozen=True)
class LiveWorkerConfig:
    """Container runtime for real workers: the image, the internal network, and the proxy URL."""

    image: str
    network: str
    proxy_url: str


def containerized_runner(
    config: LiveWorkerConfig, *, host_runner: CommandRunner = default_runner
) -> ContainerRunner:
    """Build the ``ContainerRunner`` that isolates a worker command per ADR-0007."""
    return ContainerRunner(config.image, config.network, config.proxy_url, host_runner=host_runner)


def build_containerized_worker(
    config: LiveWorkerConfig,
    *,
    family: WorkerFamily = "claude",
    host_runner: CommandRunner = default_runner,
) -> WorkerPort:
    """Build a real worker (Claude Code or Codex) whose command runs inside the container.

    ``host_runner`` is the seam that runs the assembled ``podman run`` on the host; it defaults
    to the credential-scrubbing ``default_runner`` and is injected in tests so the wiring is
    verified without launching a container or spending.
    """
    runner = containerized_runner(config, host_runner=host_runner)
    if family == "codex":
        return CodexCliWorker(runner=runner)
    return ClaudeCodeWorker(runner=runner)
