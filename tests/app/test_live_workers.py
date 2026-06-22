"""Tests for the live containerized-worker wiring (slice S16.14).

These prove the wiring without launching a container or spending: a capturing host runner
intercepts the assembled ``podman run`` command, so we can assert a real worker command is
wrapped in the isolating container (internal network + proxy, no provider keys).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from talisman_core.app.live_workers import (
    KEYLESS_PLACEHOLDER_KEY,
    LiveWorkerConfig,
    build_containerized_worker,
    keyless_gateway_env,
)
from talisman_core.ports.worker import WorkerRequest
from talisman_core.workers._subprocess import CommandResult

_CONFIG = LiveWorkerConfig(
    image="talisman/worker:latest",
    network="talisman-internal",
)


def _capturing_host_runner(
    captured: dict[str, list[str]],
) -> Callable[[list[str], Path, int, str | None], CommandResult]:
    def host_runner(
        command: list[str], cwd: Path, timeout_seconds: int, stdin_text: str | None
    ) -> CommandResult:
        captured["command"] = command
        return CommandResult(exit_code=0, stdout="ok")

    return host_runner


def _request(prompt: Path, workspace: Path, slice_id: str) -> WorkerRequest:
    return WorkerRequest(
        project_id="p",
        slice_id=slice_id,
        prompt_path=prompt,
        workspace_path=workspace,
        timeout_seconds=60,
    )


def test_containerized_claude_worker_wraps_its_command_in_the_container(tmp_path) -> None:
    """A real Claude command is wrapped in the isolating podman run (internal net + proxy only)."""
    captured: dict[str, list[str]] = {}
    worker = build_containerized_worker(
        _CONFIG, family="claude", host_runner=_capturing_host_runner(captured)
    )
    prompt = tmp_path / "plan.prompt"
    prompt.write_text("do the thing", encoding="utf-8")

    result = worker.run(_request(prompt, tmp_path, "plan"))

    cmd = captured["command"]
    assert cmd[0] == "podman"  # containerized, not run on the host
    assert "--network" in cmd
    assert "talisman-internal" in cmd  # the internal (no-egress) network
    # Provider traffic is pointed at the keyless credential gateway (ADR-0010), not a proxy.
    assert "ANTHROPIC_BASE_URL=http://talisman-gateway:8800" in cmd
    assert "OPENAI_BASE_URL=http://talisman-gateway:8801" in cmd
    assert "talisman/worker:latest" in cmd
    assert cmd[-3:] == ["claude", "-p", "do the thing"]  # the real worker command, inside
    assert result.exit_code == 0

    # The worker carries only the PLACEHOLDER key — the gateway injects the real one — so no real
    # provider secret reaches the container. Proven directly on the assembled command.
    assert f"ANTHROPIC_API_KEY={KEYLESS_PLACEHOLDER_KEY}" in cmd
    assert f"OPENAI_API_KEY={KEYLESS_PLACEHOLDER_KEY}" in cmd
    joined = " ".join(cmd)
    assert "sk-ant-" not in joined  # no real-looking Anthropic key
    for secret_var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN"):
        assert secret_var not in joined


def test_codex_family_wraps_the_codex_command_in_the_container(tmp_path) -> None:
    """The codex family wraps the codex CLI in the same isolating container."""
    captured: dict[str, list[str]] = {}
    worker = build_containerized_worker(
        _CONFIG, family="codex", host_runner=_capturing_host_runner(captured)
    )
    prompt = tmp_path / "review.prompt"
    prompt.write_text("review the diff", encoding="utf-8")

    worker.run(_request(prompt, tmp_path, "review"))

    cmd = captured["command"]
    assert cmd[0] == "podman"
    assert "talisman-internal" in cmd
    assert cmd[-4:] == ["codex", "exec", "--skip-git-repo-check", "-"]  # codex CLI, inside


def test_keyless_gateway_env_points_at_gateway_with_only_placeholder_keys() -> None:
    """The worker env points the CLIs at the gateway and carries only placeholders (ADR-0010)."""
    env = keyless_gateway_env(_CONFIG)

    assert env["ANTHROPIC_BASE_URL"] == "http://talisman-gateway:8800"
    assert env["OPENAI_BASE_URL"] == "http://talisman-gateway:8801"
    assert env["ANTHROPIC_API_KEY"] == KEYLESS_PLACEHOLDER_KEY
    assert env["OPENAI_API_KEY"] == KEYLESS_PLACEHOLDER_KEY
    # The placeholder is not a real-looking provider key — the gateway holds the real one.
    assert "sk-" not in KEYLESS_PLACEHOLDER_KEY
