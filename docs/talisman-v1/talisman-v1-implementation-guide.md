# TalisMan v1 Implementation Guide

## Document control

- **Version:** 1.1 controlled implementation baseline
- **Date:** 2026-05-26
- **Status:** Implementation baseline updated after user acceptance review.
- **Legacy source name:** The source Decision Register and Research Validation Report used the working name `clawdbot`. This document uses the implementation name **TalisMan**.
- **Accepted changes from user review:** rename system to TalisMan; keep LangGraph in v1 instead of deferring it; make two-tier workflow with user override explicit; make structural modularity mandatory; make inter-agent review mandatory; target the full Option C architecture through governed slices rather than a disposable prototype.
- **Change control:** Do not alter architecture decisions without explicit user approval and a recorded decision-audit entry.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Large Language Model (LLM), Open Web Application Security Project (OWASP), Comma-Separated Values (CSV), JavaScript Object Notation (JSON), Hypertext Transfer Protocol (HTTP), Domain Name System (DNS), Structured Query Language (SQL), Secure Shell (SSH), and Virtual Private Network (VPN) are spelled out on first use in this document.

## Prerequisites

### Hardware

- Dedicated Linux laptop, roughly five-year-old class or better.
- 16 gigabytes memory recommended; 8 gigabytes is workable for light projects.
- 50 gigabytes free disk space.
- Stable home internet.

### Subscriptions and accounts

- Anthropic Claude Pro or Max subscription for Claude Code.
- ChatGPT Plus subscription for Codex CLI access, if available to the account.
- Anthropic API key for same-family review and synthesis calls routed through the gateway.
- OpenAI API key for OpenAI-family API calls routed through the gateway.
- Telegram bot token from BotFather.
- Your Telegram numeric user ID for allowlisting.

### Budget

- Claude subscription: expected `$20/month` or higher if using Max.
- ChatGPT Plus: expected `$20/month`.
- API token budget: hard cap `$60/month`.
- v1 target total: `$100/month` before optional subscription upgrades.

### Estimated install time

Plan for one focused setup session. Do not rush the security phases. Each phase has a checkpoint that tells you what success looks like.

## Implementation strategy

TalisMan v1 targets the full Option C architecture: local-first, hardened, LangGraph-based, cross-vendor reviewed, cost-bounded, and auditable. The build must not begin as a disposable script. It must begin with the final package boundaries, final interfaces, and final test harness, then complete the architecture through governed implementation slices.

Every implementation slice must end with deterministic checks, cross-family review, and a progress-ledger update. This is how the project avoids drift while still moving quickly with Large Language Model (LLM) coding agents.

## Phase 0: Laptop preparation

### Goal

Prepare the Linux laptop with system packages, a project directory, Git, Python, container tooling, and basic firewall posture.

### Steps

1. Open a terminal.

2. Update package metadata. This tells the package manager where current packages are available.

   ```bash
   sudo apt update
   ```

3. Install base tools. `git` tracks file history, `python3-venv` creates isolated Python environments, `sqlite3` inspects the local database, `jq` formats JSON, and `curl` tests HTTP endpoints.

   ```bash
   sudo apt install -y git python3 python3-venv python3-pip sqlite3 jq curl ca-certificates gnupg lsb-release
   ```

4. Install container tooling. Prefer Podman if your distribution supports it cleanly. Docker is acceptable if Podman is not available.

   ```bash
   sudo apt install -y podman podman-compose
   ```

   If this fails because your distribution does not package `podman-compose`, install Docker Compose instead:

   ```bash
   sudo apt install -y docker.io docker-compose-plugin
   sudo usermod -aG docker "$USER"
   ```

   Log out and back in if you used Docker so group membership refreshes.

5. Create the TalisMan directory structure.

   ```bash
   mkdir -p ~/talisman/{config,state,logs,retros,projects,src,systemd,secrets,templates}
   chmod 700 ~/talisman ~/talisman/secrets
   ```

6. Initialize Git. Git is the local history and rollback mechanism for configuration and project artifacts.

   ```bash
   cd ~/talisman
   git init
   printf "secrets/\nstate/*.sqlite3\nlogs/\n.env\n" > .gitignore
   git add .gitignore
   git commit -m "Initialize TalisMan workspace"
   ```

### Troubleshooting

- If `git commit` complains about missing identity, set it locally:

  ```bash
  git config user.name "Pat Stanton"
  git config user.email "stanton.patrick0@gmail.com"
  git commit -m "Initialize TalisMan workspace"
  ```

- If `podman-compose` is missing, use Docker Compose and replace `podman-compose` commands with `docker compose` in later phases.

### Checkpoint

Run:

```bash
ls -la ~/talisman
```

You should see `config`, `state`, `logs`, `retros`, `projects`, `src`, `systemd`, `secrets`, and `templates`. Run:

```bash
git status
```

You should see a clean working tree.


## Phase 1: Architecture guardrails and repository constitution

### Goal

Create the repository skeleton that prevents architectural drift before any feature code is written.

### Steps

1. Create the repository root.

```bash
mkdir -p ~/talisman
cd ~/talisman
git init
```

2. Create the mandatory package structure.

```bash
mkdir -p src/talisman_core/{domain,ports,workflow,policies,adapters,workers,memory,security,scheduler,observability,app}
mkdir -p docs/adr docs/reviews docs/progress tests/contracts tests/architecture
find src/talisman_core -type d -exec sh -c 'touch "$0/__init__.py"' {} \;
```

3. Add the files from `talisman-v1-config-templates.md`, especially `pyproject.toml`, `.importlinter`, `AGENTS.md`, `CLAUDE.md`, and the port/interface scaffolding.

4. Install the development dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

5. Run the first architecture check.

```bash
ruff check .
mypy src/talisman_core
pytest
lint-imports
```

### Troubleshooting

- If `lint-imports` fails before feature code exists, the package tree or `.importlinter` contract names are inconsistent. Fix the contract paths before proceeding.
- If `mypy` cannot find `talisman_core`, confirm that `pyproject.toml` uses `src` package layout and the virtual environment is active.

### Checkpoint

The repository exists at `~/talisman`, all required module directories exist, and `ruff`, `mypy`, `pytest`, and `lint-imports` run successfully before implementation begins.

## Phase 2: Container and host proxy infrastructure

### Goal

Create a container boundary for TalisMan and reserve the host as the trusted place for long-lived credentials.

### Steps

1. Copy the templates from `TalisMan-v1-config-templates.md` into files under `~/talisman`. At minimum, create:

   - `config/config.yaml`
   - `docker-compose.yml`
   - `Dockerfile`
   - `config/squid.conf`
   - `systemd/talisman.service`
   - `systemd/talisman-gateway.service`
   - `src/talisman_gateway.py`
   - `src/talisman_core/main.py`
   - `pyproject.toml`

2. Create secret files. These files are intentionally not committed to Git.

   ```bash
   cd ~/talisman
   umask 077
   printf "replace-with-telegram-bot-token" > secrets/telegram_bot_token.secret
   printf "replace-with-your-telegram-user-id" > secrets/telegram_user_allowlist.secret
   printf "replace-with-anthropic-api-key" > secrets/anthropic_api_key.secret
   printf "replace-with-openai-api-key" > secrets/openai_api_key.secret
   printf "replace-with-random-shared-secret" > secrets/gateway_shared_secret.secret
   ```

3. Replace the placeholder values. The shared secret should be a long random string:

   ```bash
   python3 - <<'PY'
   import secrets
   print(secrets.token_urlsafe(48))
   PY
   ```

4. Install the host-side gateway Python environment. This gateway is the trusted local process that holds long-lived provider keys and enforces budget checks before model calls.

   ```bash
   cd ~/talisman
   python3 -m venv .venv-gateway
   . .venv-gateway/bin/activate
   pip install --upgrade pip
   pip install fastapi uvicorn httpx pydantic pyyaml
   deactivate
   ```

5. Test that the gateway scaffold starts without making provider calls.

   ```bash
   cd ~/talisman
   . .venv-gateway/bin/activate
   python src/talisman_gateway.py --self-test
   deactivate
   ```

### Troubleshooting

- If `pip install` fails, check internet access and Python version with `python3 --version`.
- If a secret file is readable by other users, fix it:

  ```bash
  chmod 600 ~/talisman/secrets/*.secret
  ```

### Checkpoint

The self-test should print:

```text
TalisMan gateway self-test passed
```

## Phase 3: TalisMan core service

### Goal

Create the Python package that will own orchestration, state transitions, scheduling, and audit logging.

### Steps

1. Create the application virtual environment.

   ```bash
   cd ~/talisman
   python3 -m venv .venv
   . .venv/bin/activate
   pip install --upgrade pip
   pip install -e ".[dev]"
   deactivate
   ```

2. Initialize the SQLite database. SQLite is the local relational database file that replaces the draft CSV lessons database.

   ```bash
   cd ~/talisman
   sqlite3 state/TalisMan.sqlite3 < src/talisman_core/memory/schema.sql
   ```

3. Verify the tables.

   ```bash
   sqlite3 state/TalisMan.sqlite3 ".tables"
   ```

4. Start the core service in dry-run mode.

   ```bash
   cd ~/talisman
   . .venv/bin/activate
   python -m talisman_core.main --config config/config.yaml --dry-run
   deactivate
   ```

### Troubleshooting

- If `pip install -e ".[dev]"` fails, make sure `pyproject.toml` exists and has valid TOML syntax.
- If SQLite reports `no such table`, rerun the schema command and check the path.

### Checkpoint

The dry run should print a startup summary that includes:

```text
configuration loaded
sqlite reachable
gateway configured
telegram disabled in dry-run
```

## Phase 4: Brain adapter via gateway

### Goal

Route every model call through the gateway so the orchestrator never directly holds provider credentials.

### Steps

1. Set the gateway URL in `config/config.yaml`:

   ```yaml
   gateway:
     base_url: "http://127.0.0.1:8787"
     mode: "host_proxy"
   ```

2. Start the gateway locally.

   ```bash
   cd ~/talisman
   . .venv-gateway/bin/activate
   uvicorn TalisMan_gateway:app --app-dir src --host 127.0.0.1 --port 8787
   ```

3. In a second terminal, test health.

   ```bash
   curl -s http://127.0.0.1:8787/health | jq
   ```

4. Stop the gateway with `Control-C` after the test.

### Troubleshooting

- If port `8787` is already in use, change `gateway.port` in `config.yaml` and the `uvicorn` command together.
- If `jq` is missing, install it with `sudo apt install -y jq`.

### Checkpoint

The health endpoint should return JSON like:

```json
{"status":"ok","service":"TalisMan-gateway"}
```

## Phase 5: Worker integration

### Goal

Teach TalisMan how to invoke Claude Code and Codex CLI without giving either worker uncontrolled access to credentials.

### Steps

1. Install Claude Code according to Anthropic’s current official instructions for your subscription.

2. Install Codex CLI according to OpenAI’s current official instructions for your subscription.

3. Record the installed versions.

   ```bash
   claude --version || true
   codex --version || true
   ```

4. Add the versions to `config/config.yaml` under `workers.expected_versions`.

5. Test subprocess invocation in dry-run mode.

   ```bash
   cd ~/talisman
   . .venv/bin/activate
   python -m talisman_core.main --config config/config.yaml --check-workers
   deactivate
   ```

### Troubleshooting

- If a command is not found, the CLI is not on your `PATH`. `PATH` is the shell’s list of directories to search for executables.
- If versions differ from `config.yaml`, update the config intentionally and commit the change.

### Checkpoint

The worker check should report both tools as found or clearly report which one is missing.

## Phase 6: Cost enforcement

### Goal

Prevent runaway agent spending before an API call occurs.

### Steps

1. Confirm budget settings in `config/config.yaml`:

   ```yaml
   budgets:
     daily_soft_usd: 5
     daily_hard_usd: 10
     monthly_hard_usd: 60
     anomaly_multiplier: 3
     anomaly_window_minutes: 15
     trailing_average_minutes: 60
   ```

2. Confirm per-call token ceilings:

   ```yaml
   gateway:
     max_tokens:
       routine: 4096
       synthesis: 8192
       deep_research: 12000
   ```

3. Run the gateway budget self-test.

   ```bash
   cd ~/talisman
   . .venv-gateway/bin/activate
   python src/talisman_gateway.py --budget-self-test
   deactivate
   ```

### Troubleshooting

- If the self-test cannot write to SQLite, check permissions on `~/talisman/state`.
- If the gateway reports missing secrets, verify `~/talisman/secrets/*.secret` exists and is mode `600`.

### Checkpoint

The self-test should show one allowed simulated call and one blocked simulated call.

## Phase 7: Memory system

### Goal

Enable cross-project learning through markdown retrospectives plus SQLite lessons.

### Steps

1. Confirm the database schema was installed:

   ```bash
   sqlite3 ~/talisman/state/TalisMan.sqlite3 ".schema lessons"
   ```

2. Insert a test lesson.

   ```bash
   sqlite3 ~/talisman/state/TalisMan.sqlite3 <<'SQL'
   INSERT INTO lessons (lesson_id, project_id, domain_tags, severity, statement, detail_ref, status, date)
   VALUES ('L-0001', 'bootstrap', 'TalisMan,testing', 'medium', 'Bootstrap should verify each phase with observable checkpoints.', 'retros/bootstrap.md', 'active', date('now'));
   SQL
   ```

3. Query it back.

   ```bash
   sqlite3 ~/talisman/state/TalisMan.sqlite3 "SELECT lesson_id, statement FROM lessons;"
   ```

4. Delete the test lesson if desired.

   ```bash
   sqlite3 ~/talisman/state/TalisMan.sqlite3 "DELETE FROM lessons WHERE lesson_id='L-0001';"
   ```

### Troubleshooting

- If the insert fails because the table already contains `L-0001`, delete it and retry.
- If SQLite reports a locked database, stop any running TalisMan process and retry.

### Checkpoint

You should see the test lesson returned by the query before deletion.

## Phase 8: Notification layer

### Goal

Enable Telegram approvals safely.

### Steps

1. Put your real Telegram bot token in:

   ```bash
   ~/talisman/secrets/telegram_bot_token.secret
   ```

2. Put your numeric Telegram user ID in:

   ```bash
   ~/talisman/secrets/telegram_user_allowlist.secret
   ```

3. Run the Telegram self-test in dry mode. This checks configuration without sending a message.

   ```bash
   cd ~/talisman
   . .venv/bin/activate
   python -m talisman_core.main --config config/config.yaml --telegram-self-test --dry-run
   deactivate
   ```

4. Run a real test message only after the dry test passes.

   ```bash
   cd ~/talisman
   . .venv/bin/activate
   python -m talisman_core.main --config config/config.yaml --telegram-self-test --send
   deactivate
   ```

### Troubleshooting

- If Telegram returns unauthorized, the bot token is wrong.
- If no message arrives, verify the bot has an open chat with you. Send `/start` to the bot in Telegram.
- If TalisMan rejects you, the allowlist user ID is wrong.

### Checkpoint

You should receive one Telegram message that says:

```text
TalisMan Telegram self-test passed
```

## Phase 9: Spiral workflow

### Goal

Create gate states, approvals, escalations, and slice tracking.

### Steps

1. Confirm the configured workflow tiers:

   ```bash
   yq '.workflow' ~/talisman/config/config.yaml 2>/dev/null || sed -n '/workflow:/,/workers:/p' ~/talisman/config/config.yaml
   ```

2. Create a test project.

   ```bash
   cd ~/talisman
   . .venv/bin/activate
   python -m talisman_core.main --config config/config.yaml --create-test-project "bootstrap-smoke-test"
   deactivate
   ```

3. Inspect the generated project state.

   ```bash
   find ~/talisman/projects/bootstrap-smoke-test -maxdepth 2 -type f -print
   ```

4. Trigger a fake approval gate.

   ```bash
   cd ~/talisman
   . .venv/bin/activate
   python -m talisman_core.main --config config/config.yaml --simulate-gate bootstrap-smoke-test interview
   deactivate
   ```

### Troubleshooting

- If `yq` is missing, the fallback `sed` command still shows the relevant block.
- If the project already exists, archive or delete it before rerunning the smoke test.

### Checkpoint

The project folder should include a state file, an audit file, and a first gate record.

## Phase 10: Red-team integration

### Goal

Verify that review routing uses cross-vendor review and optional same-family review correctly.

### Steps

1. Confirm routine and critical slice policy in `config/config.yaml`.

2. Run a dry routing simulation.

   ```bash
   cd ~/talisman
   . .venv/bin/activate
   python -m talisman_core.main --config config/config.yaml --simulate-review-routing routine
   python -m talisman_core.main --config config/config.yaml --simulate-review-routing critical
   deactivate
   ```

3. Confirm output ordering changes between repeated runs. Ordering randomization reduces judge position bias.

### Troubleshooting

- If both routes look identical, check `review.same_family_required_for_critical` and `review.same_family_optional_for_routine`.
- If randomization never changes, check whether a fixed test seed is enabled.

### Checkpoint

Routine routing should show deterministic checks plus cross-family review. Critical routing should show deterministic checks, cross-family review, and same-family review.

## Phase 11: Acceptance verification

### Goal

Ensure deterministic checks run before any LLM review.

### Steps

1. Install development dependencies.

   ```bash
   cd ~/talisman
   . .venv/bin/activate
   pip install -e ".[dev]"
   pre-commit install
   deactivate
   ```

2. Run the full deterministic check suite.

   ```bash
   cd ~/talisman
   . .venv/bin/activate
   ruff check src
   mypy src || true
   pytest -q
   pre-commit run --all-files
   deactivate
   ```

   `mypy` may initially report scaffold typing gaps. Treat those as implementation tasks before production use.

### Troubleshooting

- If `pytest` finds no tests, create at least one smoke test before using TalisMan on real work.
- If `pre-commit` modifies files, inspect the diff and rerun.

### Checkpoint

At minimum, `ruff check src` should pass before bootstrap proceeds. Production use requires tests and type checks to pass.

## Phase 12: systemd auto-restart and observability

### Goal

Run TalisMan and the gateway as managed services that restart after laptop reboot.

### Steps

1. Copy service files into the user systemd directory.

   ```bash
   mkdir -p ~/.config/systemd/user
   cp ~/talisman/systemd/talisman.service ~/.config/systemd/user/talisman.service
   cp ~/talisman/systemd/talisman-gateway.service ~/.config/systemd/user/talisman-gateway.service
   systemctl --user daemon-reload
   ```

2. Enable lingering so user services can run after login sessions end.

   ```bash
   loginctl enable-linger "$USER"
   ```

3. Start the gateway.

   ```bash
   systemctl --user start TalisMan-gateway
   systemctl --user status TalisMan-gateway --no-pager
   ```

4. Start TalisMan.

   ```bash
   systemctl --user start TalisMan
   systemctl --user status TalisMan --no-pager
   ```

5. View logs.

   ```bash
   journalctl --user -u TalisMan-gateway -n 50 --no-pager
   journalctl --user -u TalisMan -n 50 --no-pager
   ```

### Troubleshooting

- If a service exits immediately, read the last 100 log lines with `journalctl`.
- If the gateway starts but TalisMan cannot connect, verify the gateway URL in `config.yaml`.

### Checkpoint

Both services should show `active (running)` or, during dry scaffold mode, a clear intentional exit with no stack trace.

## Phase 13: Bootstrap test project

### Goal

Use TalisMan’s first project to plan its own v1.1 improvements.

### Steps

1. Create the project.

   ```bash
   cd ~/talisman
   . .venv/bin/activate
   python -m talisman_core.main --config config/config.yaml --new-project "TalisMan v1.1 improvement plan"
   deactivate
   ```

2. Select `full_spiral` because this is high-leverage infrastructure work.

3. Use this project goal:

   ```text
   Produce a v1.1 improvement plan based on v1 bootstrap telemetry, especially escalation rate, cost per slice, wait-time aging, memory retrieval quality, and sandbox hardening gaps.
   ```

4. Approve only the interview and discovery gates at first. Confirm the system can pause cleanly at the next gate.

### Troubleshooting

- If the system attempts implementation before approval, stop it and inspect the gate state. That is a serious safety bug.
- If costs accrue during a dry planning project, check that gateway pre-call accounting is enabled.

### Checkpoint

The first real project should stop at a gate and wait for Telegram approval. The audit log should show the gate, the idempotency key, and the approval state.


## Development progress control

During implementation, use the companion files generated with this package:

- `talisman-v1-master-build-roadmap.md` for phase-level control.
- `talisman-v1-slice-backlog.md` for implementation slices.
- `talisman-v1-agent-coding-protocol.md` for Claude Code and Codex CLI behavior.
- `talisman-v1-progress-ledger-template.md` for work tracking.
- `talisman-v1-acceptance-test-plan.md` for release acceptance.
- `talisman-v1-architecture-guardrails.md` for non-negotiable boundaries.

No slice is complete until its progress-ledger row is updated and the review artifact is saved in `docs/reviews/`.
