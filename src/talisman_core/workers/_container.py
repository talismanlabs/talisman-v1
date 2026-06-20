"""Containerized worker execution (slice S16.06; decision ADR-0007).

Runs a worker command inside a rootless podman container attached to an ``--internal``
network whose only reachable peer is the egress proxy. An ``--internal`` network has no
route off-host, so the worker physically cannot reach the internet except through the
proxy — it cannot bypass what it has no route to. This is the containment that turns the
egress allowlist (S16.04) from a cooperative control into a real boundary (AT-14).

``ContainerRunner`` is a drop-in ``CommandRunner``: the worker adapters are unchanged; the
composition root injects this instead of the direct ``default_runner`` for real runs. The
container starts with only an explicit, minimal environment (the proxy variables — never
the host's provider keys) and mounts only the request's workspace.
"""

from __future__ import annotations

from pathlib import Path

from talisman_core.workers._subprocess import CommandResult, CommandRunner, default_runner


class ContainerRunner:
    """A ``CommandRunner`` that executes the worker command inside an isolated container."""

    def __init__(
        self,
        image: str,
        network: str,
        proxy_url: str,
        *,
        podman: str = "podman",
        host_runner: CommandRunner = default_runner,
    ) -> None:
        """Configure the image, the (intended ``--internal``) network, and the egress proxy.

        ``host_runner`` runs the assembled ``podman run`` command on the host; it defaults
        to the credential-scrubbing ``default_runner``.
        """
        self._image = image
        self._network = network
        self._proxy_url = proxy_url
        self._podman = podman
        self._host_runner = host_runner

    def build_command(self, args: list[str], cwd: Path) -> list[str]:
        """Assemble the ``podman run`` invocation that isolates ``args`` in a container.

        The isolation lives entirely in these flags: the internal ``--network`` (no route
        out except the proxy), only the proxy variables in ``--env`` (no provider keys), and
        only the workspace mounted. Kept pure so it is unit-testable without a container.
        """
        workspace = str(cwd)
        return [
            self._podman,
            "run",
            "--rm",
            "--init",
            # Do NOT let podman inject the host's proxy variables (its default is
            # --http-proxy=true): the worker's proxy config must be exactly, and only, what
            # we set below — otherwise host proxy creds could leak in and routing is ambiguous.
            "--http-proxy=false",
            "--network",
            self._network,
            "--env",
            f"HTTPS_PROXY={self._proxy_url}",
            "--env",
            f"HTTP_PROXY={self._proxy_url}",
            "--env",
            f"https_proxy={self._proxy_url}",
            "--env",
            f"http_proxy={self._proxy_url}",
            "--env",
            "NO_PROXY=",
            "--env",
            "no_proxy=",
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
