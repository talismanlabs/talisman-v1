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

# A worker carries this as its provider API key. It is NOT a secret: the credential gateway
# (ADR-0010) overrides it with the real key on the way out, so the worker holds no real key.
# Deliberately a plain non-key string so it reads as a placeholder and never trips a scanner.
KEYLESS_PLACEHOLDER_KEY = "placeholder-gateway-injects-the-real-key"


@dataclass(frozen=True)
class LiveWorkerConfig:
    """Container runtime for real workers: the image, the sealed network, and the gateway address.

    The worker reaches the credential gateway (ADR-0010) by name on the internal network and
    nothing else; ``gateway_host``/ports locate it. There is no proxy URL — provider traffic goes
    to the gateway via the base URLs below, and the worker has no other route off-host.
    """

    image: str
    network: str
    gateway_host: str = "talisman-gateway"
    anthropic_port: int = 8800
    openai_port: int = 8801


def keyless_gateway_env(config: LiveWorkerConfig) -> dict[str, str]:
    """The worker's environment for the keyless credential gateway (ADR-0010).

    Points the Claude/Codex CLIs' provider base URLs at the gateway and sets only PLACEHOLDER
    keys — the gateway swaps in the real, host-held key. So the container holds no real provider
    secret: there is nothing for a rogue or prompt-injected worker to read or exfiltrate.
    """
    return {
        "ANTHROPIC_BASE_URL": f"http://{config.gateway_host}:{config.anthropic_port}",
        "OPENAI_BASE_URL": f"http://{config.gateway_host}:{config.openai_port}",
        "ANTHROPIC_API_KEY": KEYLESS_PLACEHOLDER_KEY,
        "OPENAI_API_KEY": KEYLESS_PLACEHOLDER_KEY,
    }


def containerized_runner(
    config: LiveWorkerConfig, *, host_runner: CommandRunner = default_runner
) -> ContainerRunner:
    """Build the ``ContainerRunner`` that isolates a worker command (ADR-0007) and points it at
    the keyless credential gateway (ADR-0010)."""
    return ContainerRunner(
        config.image, config.network, keyless_gateway_env(config), host_runner=host_runner
    )


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
