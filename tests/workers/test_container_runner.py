"""Tests for the containerized worker runner (slice S16.06, ADR-0007).

The unit tests cover the ``podman run`` invocation (always run, no container needed). The
integration test spins up a real container on a real ``--internal`` network and proves it
cannot egress — it self-skips where podman or ``--internal`` networks are unavailable, so
the deterministic gate never depends on a container runtime.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from talisman_core.workers._container import ContainerRunner


def test_build_command_isolates_the_worker_invocation(tmp_path: Path) -> None:
    """The isolation lives in the args: internal network, proxy-only env, workspace-only mount."""
    runner = ContainerRunner(
        image="talisman/worker:test", network="tm-internal", proxy_url="http://127.0.0.1:8888"
    )
    command = runner.build_command(["codex", "exec", "--skip-git-repo-check", "-"], tmp_path)

    assert command[:4] == ["podman", "run", "--rm", "--init"]
    assert command[command.index("--network") + 1] == "tm-internal"
    assert "HTTPS_PROXY=http://127.0.0.1:8888" in command
    assert "HTTP_PROXY=http://127.0.0.1:8888" in command
    # podman must NOT inherit the host's proxy vars; only our explicit (upper- + lower-case) env.
    assert "--http-proxy=false" in command
    assert "https_proxy=http://127.0.0.1:8888" in command
    # Map the host user in so the non-root worker can write the bind-mounted workspace (S16.18).
    assert "--userns=keep-id" in command
    assert f"{tmp_path}:{tmp_path}:Z" in command
    assert command[command.index("--workdir") + 1] == str(tmp_path)
    # The worker command is the tail, after the image.
    assert command[-5:] == [
        "talisman/worker:test",
        "codex",
        "exec",
        "--skip-git-repo-check",
        "-",
    ]


def test_build_command_injects_no_provider_secrets(tmp_path: Path) -> None:
    """Only the proxy variables are passed; the host's provider keys never enter the container."""
    runner = ContainerRunner(image="img", network="net", proxy_url="http://127.0.0.1:1")
    command = runner.build_command(["codex"], tmp_path)

    joined = " ".join(command)
    for secret in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN"):
        assert secret not in joined


def test_call_delegates_to_the_host_runner(tmp_path: Path) -> None:
    """``__call__`` runs the assembled podman command through the injected host runner."""
    from talisman_core.workers._subprocess import CommandResult

    seen: dict[str, object] = {}

    def fake_host_runner(
        args: list[str], cwd: Path, timeout: int, stdin: str | None
    ) -> CommandResult:
        seen["args"] = args
        seen["stdin"] = stdin
        return CommandResult(exit_code=0, stdout="ok")

    runner = ContainerRunner(
        image="img", network="net", proxy_url="http://127.0.0.1:1", host_runner=fake_host_runner
    )
    result = runner(["codex", "exec", "-"], tmp_path, 30, "the prompt")

    assert result.stdout == "ok"
    assert seen["stdin"] == "the prompt"
    assert seen["args"][:2] == ["podman", "run"]  # type: ignore[index]
    assert seen["args"][-1] == "-"  # type: ignore[index]


def _podman_internal_net_available() -> bool:
    """True iff podman can create an ``--internal`` network here (else the integration skips)."""
    if shutil.which("podman") is None:
        return False
    probe = "tm_probe_avail"
    try:
        created = subprocess.run(
            ["podman", "network", "create", "--internal", probe],
            capture_output=True,
            timeout=30,
        )
        if created.returncode != 0:
            return False
        subprocess.run(["podman", "network", "rm", probe], capture_output=True, timeout=30)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


_PODMAN_INTERNAL = _podman_internal_net_available()


@pytest.fixture
def internal_network() -> Iterator[str]:
    """A fresh podman ``--internal`` network, removed after the test."""
    name = f"tm_test_{os.getpid()}"
    subprocess.run(["podman", "network", "rm", name], capture_output=True, timeout=30)
    subprocess.run(
        ["podman", "network", "create", "--internal", name],
        capture_output=True,
        check=True,
        timeout=30,
    )
    try:
        yield name
    finally:
        subprocess.run(["podman", "network", "rm", name], capture_output=True, timeout=30)


@pytest.mark.skipif(not _PODMAN_INTERNAL, reason="podman --internal networks unavailable")
def test_container_on_internal_network_cannot_egress(internal_network: str, tmp_path: Path) -> None:
    """A real container on the internal network cannot reach the internet — the boundary is
    enforced by the network (a routing failure), not by worker cooperation (ADR-0007 / AT-14)."""
    runner = ContainerRunner(
        image="alpine:3.20", network=internal_network, proxy_url="http://unused:1"
    )
    # Actively BYPASS the proxy (unset proxy env) and connect direct — proving the block is the
    # network itself, so a worker can't escape by ignoring the proxy. This is the real claim.
    probe = [
        "sh",
        "-c",
        "unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY; "
        "wget -T5 -O /dev/null http://1.1.1.1 2>&1 || true",
    ]

    result = runner(probe, tmp_path, 60)

    # A routing failure (not a missing tool, not a proxy error) — kernel-enforced isolation.
    assert "unreachable" in result.stdout.lower(), result.stdout
