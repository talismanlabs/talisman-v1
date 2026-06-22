"""Live project run entrypoint (slice S16.22): launch the governed spiral on real workers.

Assembles the human-gated live run from operator inputs — the project goal + a workspace, the
containerized **keyless** worker (ADR-0007 containment + ADR-0010 keyless gateway, wired in S16.21),
and the Telegram approver (S16.17) built from the operator's gitignored secret files. This is the
command the operator runs on the box for the supervised first run.

Executing ``run_live`` makes real provider calls (real spend) and blocks for the operator's Telegram
approval at each gate phase — so it is a human-gated step. The builders below are pure assembly and
are unit-tested without launching a container, reaching the network, or spending.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from talisman_core.adapters.telegram.allowlist import TelegramAllowlist
from talisman_core.adapters.telegram.approver import TelegramApprover
from talisman_core.adapters.telegram.bot import TelegramBot
from talisman_core.app.live_run import run_live_project
from talisman_core.app.live_workers import (
    LiveWorkerConfig,
    WorkerFamily,
    build_containerized_worker,
)
from talisman_core.app.project_run import ProjectRunResult, ProjectSpec
from talisman_core.ports.worker import WorkerPort
from talisman_core.workflow.spiral import SPIRAL_PHASES

# Phases that block for the operator's Telegram approval in a live run. Conservative defaults: the
# two expensive/irreversible transitions — approving the plan, and approving the code work. The
# operator approves each on Telegram before the spiral proceeds; widen this for a closer watch.
DEFAULT_GATE_PHASES = frozenset({"slice_approval", "implementation"})


def _read_secret(path: Path) -> str:
    """Read a single-line secret/value from a gitignored operator file."""
    return path.read_text(encoding="utf-8").strip()


@dataclass(frozen=True)
class LiveRunConfig:
    """Everything the supervised live run needs. Secrets are read from files, never the CLI."""

    goal: str
    workspace: Path
    project_id: str = "live"
    secrets_dir: Path = Path.home() / "talisman" / "secrets"
    worker_image: str = "talisman/worker:latest"
    network: str = "talisman-internal"
    gateway_host: str = "talisman-gateway"
    family: WorkerFamily = "claude"


def build_live_spec(config: LiveRunConfig) -> ProjectSpec:
    """The project spec for the run: the full spiral, gated at the conservative default phases."""
    return ProjectSpec(
        project_id=config.project_id,
        phases=SPIRAL_PHASES,
        gate_phases=DEFAULT_GATE_PHASES,
        goal=config.goal,
    )


def build_live_worker(config: LiveRunConfig) -> WorkerPort:
    """Build the containerized keyless worker for the run.

    The worker runs inside the ``--internal``-network container (ADR-0007) and reaches providers
    only through the credential gateway carrying a placeholder key (ADR-0010) — it holds no real
    provider secret.
    """
    worker_config = LiveWorkerConfig(
        image=config.worker_image, network=config.network, gateway_host=config.gateway_host
    )
    return build_containerized_worker(worker_config, family=config.family)


def build_live_approver(secrets_dir: Path) -> TelegramApprover:
    """Build the Telegram approver from the operator's secret files (bot token + operator id).

    The operator's numeric Telegram id is both the sole allowlist entry and the chat the gates are
    posted to — a direct chat's id equals the user's id — so one id file configures both.
    """
    token = _read_secret(secrets_dir / "telegram.token")
    operator_id = int(_read_secret(secrets_dir / "telegram.operator_id"))
    bot = TelegramBot(token, TelegramAllowlist(frozenset({operator_id})))
    return TelegramApprover(bot, operator_id)


def run_live(config: LiveRunConfig) -> ProjectRunResult:
    """Assemble and run the supervised live project: real workers + gateway + Telegram. Real spend.

    Thin composition over the builders above (each independently tested); calling it is the
    human-gated live run, so it is not exercised by the deterministic gate.
    """
    config.workspace.mkdir(parents=True, exist_ok=True)
    worker = build_live_worker(config)
    approver = build_live_approver(config.secrets_dir)
    spec = build_live_spec(config)
    return run_live_project(spec, worker=worker, workspace=config.workspace, approver=approver)
