"""Containerized worker execution (slice S16.06; decision ADR-0007).

Runs a worker command inside a rootless podman container attached to an ``--internal``
network whose only reachable peer is the egress proxy. An ``--internal`` network has no
route off-host, so the worker physically cannot reach the internet except through the
proxy — it cannot bypass what it has no route to. This is the containment that turns the
egress allowlist (S16.04) from a cooperative control into a real boundary (AT-14).

``ContainerRunner`` is a drop-in ``CommandRunner``: the worker adapters are unchanged; the
composition root injects this instead of the direct ``default_runner`` for real runs. The
container starts with only an explicit, minimal environment (exactly the ``env`` mapping the
composition passes — never inherited from the host, never a real provider key) and mounts only
the request's workspace. For the keyless-gateway live run (ADR-0010) that env is the provider
base URLs pointed at the credential gateway plus *placeholder* keys the gateway overrides.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from talisman_core.workers._subprocess import CommandResult, CommandRunner, default_runner


class ContainerRunner:
    """A ``CommandRunner`` that executes the worker command inside an isolated container."""

    def __init__(
        self,
        image: str,
        network: str,
        env: Mapping[str, str],
        *,
        podman: str = "podman",
        host_runner: CommandRunner = default_runner,
    ) -> None:
        """Configure the image, the (intended ``--internal``) network, and the worker's env.

        ``env`` is the *complete*, explicit set of environment variables the worker container
        receives — nothing is inherited from the host (``--http-proxy=false`` stops podman
        injecting even the host proxy vars). For the keyless-gateway live run (ADR-0010) this is
        the provider base URLs (pointed at the gateway) plus PLACEHOLDER keys the gateway
        overrides; no real provider secret is ever placed here. ``host_runner`` runs the
        assembled command on the host; it defaults to the credential-scrubbing ``default_runner``.
        """
        self._image = image
        self._network = network
        self._env = dict(env)
        self._podman = podman
        self._host_runner = host_runner

    def build_command(self, args: list[str], cwd: Path) -> list[str]:
        """Assemble the ``podman run`` invocation that isolates ``args`` in a container.

        The isolation lives entirely in these flags: the internal ``--network`` (no route out
        except its one reachable peer), exactly the explicit ``--env`` we pass (no host
        inheritance, no real provider key), and only the workspace mounted. Kept pure so it is
        unit-testable without a container.
        """
        workspace = str(cwd)
        env_flags: list[str] = []
        for key, value in sorted(self._env.items()):
            env_flags += ["--env", f"{key}={value}"]
        return [
            self._podman,
            "run",
            "--rm",
            "--init",
            # Map the host user into the container so the non-root worker can WRITE the
            # bind-mounted workspace (rootless podman). Without this the worker's container UID
            # maps to an unprivileged subuid that cannot write host-owned files, so a real
            # worker's branch-and-commit would fail with permission errors. Verified in S16.18.
            "--userns=keep-id",
            # Do NOT let podman inject the host's proxy variables (its default is
            # --http-proxy=true): the worker's environment must be exactly, and only, what we
            # pass below — otherwise host proxy creds could leak in and routing is ambiguous.
            "--http-proxy=false",
            "--network",
            self._network,
            *env_flags,
            "--volume",
            f"{workspace}:{workspace}:Z",
            "--workdir",
            workspace,
            "--interactive",
            self._image,
            *args,
        ]

    def __call__(
        self, args: list[str], cwd: Path, timeout_seconds: int, stdin_text: str | None = None
    ) -> CommandResult:
        """Run ``args`` inside the isolated container and return the captured result."""
        command = self.build_command(args, cwd)
        return self._host_runner(command, cwd, timeout_seconds, stdin_text)
