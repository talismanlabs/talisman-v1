# TalisMan v1 Configuration Templates

## Document control

- **Version:** 1.1 controlled implementation baseline
- **Date:** 2026-05-26
- **Status:** Implementation baseline updated after user acceptance review.
- **Legacy source name:** The source Decision Register and Research Validation Report used the working name `clawdbot`. This document uses the implementation name **TalisMan**.
- **Accepted changes from user review:** rename system to TalisMan; keep LangGraph in v1 instead of deferring it; make two-tier workflow with user override explicit; make structural modularity mandatory; make inter-agent review mandatory; target the full Option C architecture through governed slices rather than a disposable prototype.
- **Change control:** Do not alter architecture decisions without explicit user approval and a recorded decision-audit entry.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Large Language Model (LLM), Open Web Application Security Project (OWASP), Comma-Separated Values (CSV), JavaScript Object Notation (JSON), Hypertext Transfer Protocol (HTTP), Domain Name System (DNS), Structured Query Language (SQL), Secure Shell (SSH), and Virtual Private Network (VPN) are spelled out on first use in this document.

## File: `~/talisman/config/config.yaml`

```yaml
# TalisMan v1 configuration.
# This file contains policy and non-secret settings only.
# Do not place provider API keys, Telegram bot tokens, passwords, or private keys here.

version: 1

paths:
  root: "~/talisman"
  state_db: "~/talisman/state/TalisMan.sqlite3"
  projects_dir: "~/talisman/projects"
  retros_dir: "~/talisman/retros"
  logs_dir: "~/talisman/logs"

orchestrator:
  substrate: "langgraph"
  service_mode: "systemd"
  daily_escalation_budget: 6
  disagreement_threshold: 0.70
  # Irreversible actions always require approval even if disagreement is below threshold.
  irreversible_actions_require_approval: true

workflow:
  # Research-aligned default. User override: set allow_lightweight to false.
  allow_lightweight: true
  default_tier: "full_spiral"
  tiers:
    lightweight:
      gates: ["interview", "plan", "slice_approval", "review", "retro"]
      auto_pass: ["discovery", "red_team"]
    full_spiral:
      gates: ["interview", "discovery", "synthesis", "plan", "red_team", "slice_approval", "implementation", "review", "retro"]
      auto_pass: []

telegram:
  enabled: true
  # Token and allowlist are read from secret files, not from this YAML file.
  token_secret_file: "~/talisman/secrets/telegram_bot_token.secret"
  allowlist_secret_file: "~/talisman/secrets/telegram_user_allowlist.secret"
  approval_idempotency_ttl_hours: 72
  tolerate_message_reordering: true

workers:
  invocation: "subprocess"
  cli_version_pin_required: true
  expected_versions:
    claude_code: "record-after-install"
    codex_cli: "record-after-install"
  timeouts_seconds:
    routine: 300
    deep_research: 1800
  environment_scrub:
    enabled: true
    variables:
      - "ANTHROPIC_API_KEY"
      - "OPENAI_API_KEY"
      - "AWS_ACCESS_KEY_ID"
      - "AWS_SECRET_ACCESS_KEY"
      - "GITHUB_TOKEN"

review:
  cross_family_required: true
  same_family_required_for_critical: true
  same_family_optional_for_routine: true
  randomize_reviewer_order: true
  strip_provenance_during_first_pass: true

budgets:
  daily_soft_usd: 5
  daily_hard_usd: 10
  monthly_hard_usd: 60
  default_project_soft_usd: 25
  anomaly_multiplier: 3
  anomaly_window_minutes: 15
  trailing_average_minutes: 60

retry:
  base_delay_seconds: 1
  max_delay_seconds: 30
  max_attempts: 3
  full_jitter: true
  honor_retry_after: true
  retryable_http_statuses: [408, 429, 500, 502, 503, 504]

portfolio:
  active_worker_slots: 3
  default_priority: "medium"
  aging_promotion_after_hours: 24
  heartbeat_seconds: 30
  stuck_after_missed_heartbeats: 3

memory:
  store: "sqlite"
  embedding_upgrade_lesson_count: 50
  retrospective_template: "~/talisman/templates/retrospective.md"

security:
  container_runtime: "podman"
  credentials_mode: "host_proxy"
  egress_mode: "allowlist_proxy"
  allow_unrecommended_overrides: false
  egress_allowlist:
    - "api.anthropic.com"
    - "api.openai.com"
    - "api.telegram.org"
    - "github.com"
    - "objects.githubusercontent.com"
    - "raw.githubusercontent.com"
    - "pypi.org"
    - "files.pythonhosted.org"
    - "deb.debian.org"
    - "archive.ubuntu.com"
    - "security.ubuntu.com"

gateway:
  base_url: "http://127.0.0.1:8787"
  mode: "host_proxy"
  shared_secret_file: "~/talisman/secrets/gateway_shared_secret.secret"
  max_tokens:
    routine: 4096
    synthesis: 8192
    deep_research: 12000
```

## File: `~/talisman/.env.template`

```bash
# Non-secret environment template for local shell convenience.
# Copy to .env only if a command needs these values.
# Never place provider API keys or Telegram bot tokens in this file.

TALISMAN_HOME="$HOME/TalisMan"
TALISMAN_CONFIG="$HOME/TalisMan/config/config.yaml"
TALISMAN_GATEWAY_URL="http://127.0.0.1:8787"
PYTHONUNBUFFERED="1"
```

## File: `~/talisman/docker-compose.yml`

```yaml
version: "3.9"

services:
  talisman-core:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: talisman-core
    restart: unless-stopped
    command: ["python", "-m", "talisman_core.main", "--config", "/app/config/config.yaml"]
    volumes:
      - ./config:/app/config:ro
      - ./projects:/app/projects
      - ./retros:/app/retros
      - ./state:/app/state
      - ./logs:/app/logs
    environment:
      # Non-secret settings only. Provider credentials are intentionally absent.
      TALISMAN_CONFIG: "/app/config/config.yaml"
      HTTP_PROXY: "http://egress-proxy:3128"
      HTTPS_PROXY: "http://egress-proxy:3128"
      NO_PROXY: "localhost,127.0.0.1,host.docker.internal"
      CLAUDE_CODE_SUBPROCESS_ENV_SCRUB: "1"
    extra_hosts:
      # Lets the container reach the host-side gateway without giving it general host access.
      - "host.docker.internal:host-gateway"
    networks:
      - talisman_internal
    depends_on:
      - egress-proxy

  egress-proxy:
    image: ubuntu/squid:latest
    container_name: talisman-egress-proxy
    restart: unless-stopped
    volumes:
      - ./config/squid.conf:/etc/squid/squid.conf:ro
    networks:
      - talisman_internal
      - talisman_egress

networks:
  talisman_internal:
    internal: true
  talisman_egress:
    internal: false
```

## File: `~/talisman/Dockerfile`

```dockerfile
FROM python:3.12-slim

# Install only runtime tools needed by the orchestrator.
# Worker Command Line Interface tools may be mounted or installed during bootstrap after version pinning.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

USER nobody
```

## File: `~/talisman/config/squid.conf`

```conf
# Squid egress proxy allowlist for TalisMan.
# The worker container should send Hypertext Transfer Protocol and secure Hypertext Transfer Protocol traffic through this proxy.
# Direct network egress should be blocked by container networking and later by stricter firewall rules.

http_port 3128

acl SSL_ports port 443
acl Safe_ports port 80
acl Safe_ports port 443
acl CONNECT method CONNECT

acl allowed_domains dstdomain \
  .anthropic.com \
  .openai.com \
  .telegram.org \
  .github.com \
  .githubusercontent.com \
  .pypi.org \
  .pythonhosted.org \
  .debian.org \
  .ubuntu.com

http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports
http_access allow allowed_domains
http_access deny all

access_log stdio:/var/log/squid/access.log
cache_log /var/log/squid/cache.log
```

## File: `~/talisman/systemd/talisman-gateway.service`

```ini
[Unit]
Description=TalisMan host-side credential and budget gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/TalisMan
ExecStart=%h/TalisMan/.venv-gateway/bin/uvicorn TalisMan_gateway:app --app-dir %h/TalisMan/src --host 127.0.0.1 --port 8787
Restart=on-failure
RestartSec=5
Environment=TALISMAN_HOME=%h/TalisMan

# Secrets are file-based and not committed to Git. For stronger hardening, migrate these to systemd LoadCredential.
ReadWritePaths=%h/TalisMan/state %h/TalisMan/logs
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
```

## File: `~/talisman/systemd/talisman.service`

```ini
[Unit]
Description=TalisMan orchestration service
After=talisman-gateway.service
Wants=talisman-gateway.service

[Service]
Type=simple
WorkingDirectory=%h/TalisMan
ExecStart=%h/TalisMan/.venv/bin/python -m talisman_core.main --config %h/TalisMan/config/config.yaml
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

# Keep the service constrained to the TalisMan workspace.
ReadWritePaths=%h/TalisMan
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
```

## File: `~/talisman/pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "talisman-core"
version = "0.1.0"
description = "Local-first personal Artificial Intelligence orchestration system"
requires-python = ">=3.11"
dependencies = [
  "pydantic>=2.7",
  "pyyaml>=6.0",
  "httpx>=0.27",
  "fastapi>=0.111",
  "uvicorn>=0.30",
  "langgraph>=0.2",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2",
  "ruff>=0.5",
  "mypy>=1.10",
  "import-linter>=2.0",
  "pre-commit>=3.7",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]

[tool.mypy]
python_version = "3.11"
warn_unused_configs = true
strict = true
ignore_missing_imports = true
mypy_path = "src"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
```

## File: `~/talisman/.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: []
  - repo: local
    hooks:
      - id: import-linter
        name: import-linter architecture contracts
        entry: lint-imports
        language: system
        pass_filenames: false
```



## File: `~/talisman/.importlinter`

```ini
[importlinter]
root_package = talisman_core

[importlinter:contract:domain_is_pure]
name = Domain layer must remain pure
kind = forbidden
source_modules =
    talisman_core.domain
forbidden_modules =
    talisman_core.adapters
    talisman_core.workers
    talisman_core.security
    talisman_core.memory
    talisman_core.observability
    talisman_core.app

[importlinter:contract:workflow_uses_ports_not_adapters]
name = Workflow must depend on ports, not concrete adapters
kind = forbidden
source_modules =
    talisman_core.workflow
forbidden_modules =
    talisman_core.adapters
    talisman_core.workers

[importlinter:contract:policies_do_not_call_infrastructure]
name = Policies must not call infrastructure
kind = forbidden
source_modules =
    talisman_core.policies
forbidden_modules =
    talisman_core.adapters
    talisman_core.workers
    talisman_core.app

[importlinter:contract:app_is_composition_root]
name = Only app wires concrete implementations
kind = forbidden
source_modules =
    talisman_core.domain
    talisman_core.workflow
    talisman_core.policies
    talisman_core.ports
forbidden_modules =
    talisman_core.app
```

## File: `~/talisman/AGENTS.md`

```markdown
# TalisMan Agent Instructions

These rules apply to every Large Language Model (LLM) coding agent working in this repository.

## Non-negotiable architecture rules

1. Do not bypass ports. Core workflow code talks to `talisman_core.ports`, not concrete vendors.
2. Do not import adapters from `domain`, `workflow`, or `policies`.
3. Do not place business rules inside Telegram, SQLite, LiteLLM, Claude Code, or Codex adapters.
4. Do not store secrets in source files, `.env`, configuration YAML, logs, tests, or prompts.
5. Do not perform irreversible actions without an explicit approval gate.
6. Do not mark a slice complete without `ruff`, `mypy`, `pytest`, and `lint-imports` passing.
7. Do not mark a slice complete without opposite-family review saved under `docs/reviews/`.
8. Any architecture-boundary exception requires an Architecture Decision Record (ADR).

## Required slice completion record

Every slice must update `docs/progress/progress-ledger.md` with: slice identifier, lead agent, review agent, tests run, architecture checks, artifacts changed, open risks, and next action.
```

## File: `~/talisman/CLAUDE.md`

```markdown
# Claude Code Instructions for TalisMan

Claude Code may implement repository changes, but it must preserve the TalisMan architecture.

Before changing code, read:

1. `AGENTS.md`
2. `docs/architecture-guardrails.md`
3. The active slice in `docs/slice-backlog.md`
4. Any relevant Architecture Decision Record (ADR)

Claude Code must produce small, reviewable diffs and must not collapse module boundaries for convenience. If the requested change appears to require a boundary violation, stop and propose an Architecture Decision Record instead.
```

## File: `~/talisman/src/talisman_core/domain/project.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class WorkflowTier(str, Enum):
    """Supported workflow intensity levels.

    The tier controls review depth and gate count. The user may override the
    recommended tier because TalisMan is a human-governed assistant, not an
    autonomous authority.
    """

    LIGHTWEIGHT = "lightweight"
    FULL_SPIRAL = "full_spiral"


@dataclass(frozen=True)
class Project:
    """Immutable description of a TalisMan project.

    The domain model intentionally contains no Telegram, SQLite, LangGraph,
    or worker-specific behavior. This keeps the project concept portable across
    interfaces and future implementations.
    """

    project_id: str
    title: str
    tier: WorkflowTier
    root_path: Path
```

## File: `~/talisman/src/talisman_core/ports/worker.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class WorkerRequest:
    """Structured request sent to an external coding or reasoning worker."""

    project_id: str
    slice_id: str
    prompt_path: Path
    workspace_path: Path
    timeout_seconds: int


@dataclass(frozen=True)
class WorkerResult:
    """Structured result returned by a worker adapter.

    The orchestrator stores results as artifacts. It must not blindly execute
    worker-generated commands without going through the approval and review
    gates required by policy.
    """

    worker_name: str
    exit_code: int
    transcript_path: Path
    artifact_paths: tuple[Path, ...]
    summary: str


class WorkerPort(Protocol):
    """Interface implemented by Claude Code, Codex CLI, and future workers."""

    def run(self, request: WorkerRequest) -> WorkerResult:
        """Run one worker task and return a structured, auditable result."""
```

## File: `~/talisman/src/talisman_core/ports/approval.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ApprovalDecision(str, Enum):
    """Possible user decisions at a human approval gate."""

    APPROVE = "approve"
    REVISE = "revise"
    PAUSE = "pause"
    REJECT = "reject"


@dataclass(frozen=True)
class ApprovalRequest:
    """Approval request shown to the user through an interface adapter."""

    project_id: str
    gate_id: str
    message: str
    idempotency_key: str


class ApprovalPort(Protocol):
    """Interface for human approval systems such as Telegram or a future dashboard."""

    def request_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        """Ask the user for a decision and return the normalized response."""
```

## File: `~/talisman/src/talisman_core/workflow/spiral.py`

```python
from __future__ import annotations

from typing import TypedDict


class SpiralState(TypedDict):
    """Serializable LangGraph state for one project spiral.

    Keep this state intentionally boring: strings, booleans, numbers, and lists.
    Durable checkpointing is easier to debug when state is plain and auditable.
    """

    project_id: str
    tier: str
    current_phase: str
    pending_gate_id: str | None
    artifacts: list[str]
    escalations_today: int


def build_spiral_graph():
    """Build the LangGraph workflow for TalisMan's gated spiral.

    The function is deliberately kept separate from application wiring. It should
    define graph shape and transitions, while external effects enter through
    ports supplied by the application composition root.
    """

    # The first implementation slice should replace this placeholder with a
    # real LangGraph StateGraph while preserving the plain `SpiralState` schema.
    raise NotImplementedError("LangGraph spiral graph is implemented in the workflow slice.")
```

## File: `~/talisman/tests/architecture/test_import_boundaries.py`

```python
"""Architecture smoke tests.

Import Linter performs the authoritative import-boundary check. This pytest file
exists so test output reminds future contributors that architecture is tested on
purpose, not by accident.
"""


def test_architecture_boundaries_are_tested_by_import_linter() -> None:
    """Keep an explicit architecture test in the normal pytest suite."""

    assert True
```

## File: `~/talisman/src/talisman_gateway.py`

```python
"""Host-side credential and budget gateway for TalisMan.

This scaffold deliberately keeps long-lived provider credentials outside the worker
container. The gateway is the correct place for budget checks because an agent that is
buggy, compromised, or prompt-injected cannot be trusted to enforce its own spending.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(title="TalisMan gateway", version="0.1.0")


@dataclass(frozen=True)
class GatewayPaths:
    """Filesystem locations used by the gateway.

    The gateway reads secrets from files with restrictive permissions and writes budget
    audit events to SQLite. File paths are kept explicit to make troubleshooting simple.
    """

    home: Path
    state_db: Path
    shared_secret: Path
    anthropic_key: Path
    openai_key: Path

    @classmethod
    def from_environment(cls) -> "GatewayPaths":
        """Build paths from the TALISMAN_HOME environment variable."""

        home = Path(os.environ.get("TALISMAN_HOME", "~/talisman")).expanduser()
        return cls(
            home=home,
            state_db=home / "state" / "TalisMan.sqlite3",
            shared_secret=home / "secrets" / "gateway_shared_secret.secret",
            anthropic_key=home / "secrets" / "anthropic_api_key.secret",
            openai_key=home / "secrets" / "openai_api_key.secret",
        )


class ModelRequest(BaseModel):
    """Minimal model request accepted by the gateway scaffold.

    A production implementation should translate this request into the selected provider
    or LiteLLM request format after budget checks pass.
    """

    provider: str = Field(description="Model provider family, for example anthropic or openai")
    model: str = Field(description="Provider model name")
    task_profile: str = Field(default="routine", description="routine, synthesis, or deep_research")
    max_tokens: int = Field(default=4096, ge=1)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    messages: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a simple health response for service checks."""

    return {"status": "ok", "service": "TalisMan-gateway"}


@app.post("/v1/model")
def model_proxy(request: ModelRequest, x_TalisMan_gateway_secret: str | None = Header(None)) -> dict[str, Any]:
    """Validate budget and proxy a model request.

    This scaffold intentionally does not make a live provider call. That avoids accidental
    spend during bootstrap. The next implementation slice should replace the placeholder
    response with a LiteLLM-compatible proxy call after the budget check succeeds.
    """

    paths = GatewayPaths.from_environment()
    expected_secret = read_secret(paths.shared_secret)
    if not expected_secret or x_TalisMan_gateway_secret != expected_secret:
        raise HTTPException(status_code=401, detail="gateway secret mismatch")

    ensure_budget_allowed(paths.state_db, request.estimated_cost_usd)
    record_budget_event(paths.state_db, request.provider, request.model, request.estimated_cost_usd)

    return {
        "status": "accepted_by_gateway_scaffold",
        "provider": request.provider,
        "model": request.model,
        "note": "Replace scaffold response with provider or LiteLLM forwarding after bootstrap tests pass.",
    }


def read_secret(path: Path) -> str:
    """Read a secret from a local file and strip trailing whitespace.

    Secret files are used instead of environment variables so subprocesses do not inherit
    long-lived credentials by default.
    """

    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def ensure_budget_allowed(db_path: Path, estimated_cost_usd: float) -> None:
    """Raise an error if a simulated request should be blocked by budget policy."""

    if estimated_cost_usd > 10.0:
        raise HTTPException(status_code=402, detail="simulated call exceeds hard daily cap")
    db_path.parent.mkdir(parents=True, exist_ok=True)


def record_budget_event(db_path: Path, provider: str, model: str, cost_usd: float) -> None:
    """Persist a budget event so cost accounting can be audited later."""

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS budget_events ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "provider TEXT NOT NULL, model TEXT NOT NULL, cost_usd REAL NOT NULL, "
            "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute(
            "INSERT INTO budget_events (provider, model, cost_usd) VALUES (?, ?, ?)",
            (provider, model, cost_usd),
        )


def run_self_test() -> None:
    """Run non-network checks that verify basic gateway wiring."""

    paths = GatewayPaths.from_environment()
    paths.home.mkdir(parents=True, exist_ok=True)
    paths.state_db.parent.mkdir(parents=True, exist_ok=True)
    print("TalisMan gateway self-test passed")


def run_budget_self_test() -> None:
    """Exercise allowed and blocked budget paths without spending money."""

    paths = GatewayPaths.from_environment()
    ensure_budget_allowed(paths.state_db, 1.0)
    record_budget_event(paths.state_db, "self-test", "allowed", 1.0)
    try:
        ensure_budget_allowed(paths.state_db, 11.0)
    except HTTPException:
        print("blocked simulated call over hard cap")
    print("budget self-test passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TalisMan gateway utility")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--budget-self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
    elif args.budget_self_test:
        run_budget_self_test()
    else:
        parser.print_help()
```



## File: `~/talisman/src/talisman_core/__init__.py`

```python
"""TalisMan package.

The package marker makes local editable installs predictable for novice bootstrap work.
"""

__version__ = "0.1.0"
```

## File: `~/talisman/src/talisman_core/brain/__init__.py`

```python
"""Brain adapter package for provider-neutral model calls."""
```

## File: `~/talisman/src/talisman_core/security/__init__.py`

```python
"""Security helpers for retry policy, credentials, and sandbox boundaries."""
```

## File: `~/talisman/src/talisman_core/memory/__init__.py`

```python
"""Memory package for SQLite-backed lessons and project retrospectives."""
```

## File: `~/talisman/src/talisman_core/main.py`

```python
"""TalisMan orchestration entry point.

This module is intentionally small. Startup should validate configuration, verify state
storage, check worker availability, and then hand execution to the workflow engine. Keeping
startup boring makes failures easier for a novice operator to diagnose.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any

import yaml


class TalismanConfigError(RuntimeError):
    """Raised when configuration is missing or unsafe."""


def expand_path(raw: str) -> Path:
    """Expand a user-facing path such as ~/talisman into an absolute Path."""

    return Path(raw).expanduser().resolve()


def load_config(path: Path) -> dict[str, Any]:
    """Load YAML configuration and fail clearly if the file is missing."""

    if not path.exists():
        raise TalismanConfigError(f"configuration file not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def check_sqlite(config: dict[str, Any]) -> None:
    """Verify that the configured SQLite database can be opened."""

    db_path = expand_path(config["paths"]["state_db"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("SELECT 1")


def check_workers() -> dict[str, str]:
    """Return detected worker Command Line Interface paths.

    The function does not fail if a worker is missing because bootstrap may install workers
    later. The caller decides whether missing workers are fatal for the current mode.
    """

    return {
        "claude_code": shutil.which("claude") or "missing",
        "codex_cli": shutil.which("codex") or "missing",
    }


def create_test_project(config: dict[str, Any], name: str) -> Path:
    """Create a minimal project folder for smoke testing gate persistence."""

    slug = name.lower().replace(" ", "-")
    project_dir = expand_path(config["paths"]["projects_dir"]) / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    state = {"project_id": slug, "name": name, "current_gate": "interview", "status": "created"}
    (project_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    (project_dir / "audit.log").write_text("project created\n", encoding="utf-8")
    return project_dir


def main() -> int:
    """Parse command-line arguments and run bootstrap-safe actions."""

    parser = argparse.ArgumentParser(description="TalisMan orchestration service")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check-workers", action="store_true")
    parser.add_argument("--create-test-project")
    parser.add_argument("--simulate-gate", nargs=2, metavar=("PROJECT", "GATE"))
    parser.add_argument("--simulate-review-routing", choices=["routine", "critical"])
    parser.add_argument("--telegram-self-test", action="store_true")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--new-project")
    args = parser.parse_args()

    config = load_config(expand_path(args.config))
    check_sqlite(config)

    if args.dry_run:
        print("configuration loaded")
        print("sqlite reachable")
        print("gateway configured")
        print("telegram disabled in dry-run")
        return 0

    if args.check_workers:
        print(json.dumps(check_workers(), indent=2))
        return 0

    if args.create_test_project:
        project_dir = create_test_project(config, args.create_test_project)
        print(f"created test project: {project_dir}")
        return 0

    if args.simulate_gate:
        project, gate = args.simulate_gate
        print(f"simulated gate {gate} for project {project}; waiting for approval")
        return 0

    if args.simulate_review_routing:
        if args.simulate_review_routing == "routine":
            print("routine: deterministic checks -> cross-family review -> synthesis")
        else:
            print("critical: deterministic checks -> cross-family review -> same-family review -> synthesis")
        return 0

    if args.telegram_self_test:
        if args.send:
            print("Telegram send scaffold: implement bot API call after token verification")
        else:
            print("Telegram dry self-test passed")
        return 0

    if args.new_project:
        project_dir = create_test_project(config, args.new_project)
        print(f"new project created: {project_dir}")
        return 0

    print("TalisMan scaffold started; implement LangGraph loop in next slice")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## File: `~/talisman/src/talisman_core/brain/adapter.py`

```python
"""Vendor-agnostic brain adapter for TalisMan.

The adapter hides provider-specific Application Programming Interface details from the
orchestrator. This protects vendor agility and ensures every model call goes through the
budget gateway before money is spent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class BrainRequest:
    """Provider-neutral request passed from orchestration policy to the gateway."""

    provider: str
    model: str
    task_profile: str
    messages: list[dict[str, Any]]
    estimated_cost_usd: float = 0.0
    max_tokens: int = 4096


class BrainAdapter:
    """Send model requests through the TalisMan gateway.

    The adapter deliberately knows only the gateway URL and shared secret. It does not know
    provider API keys, which keeps long-lived credentials out of the orchestrator process.
    """

    def __init__(self, base_url: str, gateway_secret: str) -> None:
        """Store connection details for future model requests."""

        self.base_url = base_url.rstrip("/")
        self.gateway_secret = gateway_secret

    def complete(self, request: BrainRequest) -> dict[str, Any]:
        """Submit a model request to the gateway and return parsed JSON."""

        response = httpx.post(
            f"{self.base_url}/v1/model",
            headers={"X-Talisman-Gateway-Secret": self.gateway_secret},
            json=request.__dict__,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
```

## File: `~/talisman/src/talisman_core/security/retry.py`

```python
"""Retry helpers for transient model and network failures.

The important design point is full jitter. Without jitter, multiple agents can retry at the
same time and create a thundering herd against the provider.
"""

from __future__ import annotations

import random
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone


RETRYABLE_HTTP_STATUSES = {408, 429, 500, 502, 503, 504}


def compute_full_jitter_delay(attempt: int, base_seconds: float, max_seconds: float) -> float:
    """Return a randomized exponential backoff delay using full jitter."""

    exponential_cap = min(max_seconds, base_seconds * (2 ** attempt))
    return random.uniform(0, exponential_cap)


def retry_after_seconds(header_value: str | None) -> float | None:
    """Parse a Retry-After header into seconds when possible."""

    if not header_value:
        return None
    if header_value.isdigit():
        return float(header_value)
    try:
        retry_time = parsedate_to_datetime(header_value)
    except (TypeError, ValueError):
        return None
    now = datetime.now(timezone.utc)
    return max(0.0, (retry_time - now).total_seconds())


def should_retry(status_code: int | None, network_error: bool = False) -> bool:
    """Return True only for documented retryable failures."""

    return network_error or status_code in RETRYABLE_HTTP_STATUSES
```

## File: `~/talisman/src/talisman_core/memory/schema.sql`

```sql
-- SQLite schema for TalisMan v1.
-- SQLite replaces the draft CSV store so lesson updates are transactional and auditable.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('lightweight', 'full_spiral')),
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lessons (
    lesson_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    domain_tags TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    statement TEXT NOT NULL,
    detail_ref TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'retracted', 'superseded')),
    date TEXT NOT NULL,
    supersedes_lesson_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supersedes_lesson_id) REFERENCES lessons(lesson_id)
);

CREATE TABLE IF NOT EXISTS lesson_audit (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id)
);

CREATE TABLE IF NOT EXISTS gate_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scheduler_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    priority TEXT NOT NULL,
    enqueued_at TEXT NOT NULL,
    started_at TEXT,
    total_wait_seconds INTEGER NOT NULL DEFAULT 0,
    last_wait_reason TEXT
);
```

## File: `~/talisman/templates/retrospective.md`

```markdown
# Project Retrospective: <project-name>

## Metadata

- Project ID:
- Tier:
- Start date:
- End date:
- Lead worker:
- Review workers:

## Original Goal

State the goal as approved at intake.

## Outcome Summary

Describe what was completed and what was not completed.

## What Worked

List practices, prompts, tools, and gates that improved the outcome.

## What Failed

List failures without blame. Focus on causes and safeguards.

## Surprises

Capture unexpected constraints, costs, risks, or discoveries.

## Lessons

Cross-reference each lesson ID in SQLite.

## Open Questions

List unresolved questions for future cycles.

## Recommendations for Future Projects

Convert the retrospective into practical guidance for the next intake.
```
