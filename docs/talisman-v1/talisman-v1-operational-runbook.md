# TalisMan v1 Operational Runbook

## Document control

- **Version:** 1.1 controlled implementation baseline
- **Date:** 2026-05-26
- **Status:** Implementation baseline updated after user acceptance review.
- **Legacy source name:** The source Decision Register and Research Validation Report used the working name `clawdbot`. This document uses the implementation name **TalisMan**.
- **Accepted changes from user review:** rename system to TalisMan; keep LangGraph in v1 instead of deferring it; make two-tier workflow with user override explicit; make structural modularity mandatory; make inter-agent review mandatory; target the full Option C architecture through governed slices rather than a disposable prototype.
- **Change control:** Do not alter architecture decisions without explicit user approval and a recorded decision-audit entry.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Large Language Model (LLM), Open Web Application Security Project (OWASP), Comma-Separated Values (CSV), JavaScript Object Notation (JSON), Hypertext Transfer Protocol (HTTP), Domain Name System (DNS), Structured Query Language (SQL), Secure Shell (SSH), and Virtual Private Network (VPN) are spelled out on first use in this document.

## Operating principle

TalisMan is governed by architecture documents and progress ledgers. Day-to-day operation should be hands-off except for approval gates, escalations, cost events, incidents, and deliberate maintenance. During TalisMan self-improvement, every development slice must update the progress ledger and save cross-vendor review evidence.

## Starting a new project

### Telegram commands

Use these commands from the allowlisted Telegram account only.

```text
/new_project
/status
/projects
/pause <project-id>
/resume <project-id>
/archive <project-id>
/priority <project-id> <high|medium|low>
/costs
/help
```

### Intake interview flow

1. Send `/new_project`.
2. Provide a plain-English goal.
3. Answer the stakes question: what happens if the project goes wrong?
4. Answer the novelty question: how uncertain or unfamiliar is the work?
5. Review TalisMan’s recommended tier: `lightweight` or `full_spiral`.
6. Approve or override the tier.
7. Approve the proposed per-project soft budget.
8. Wait for the first gate artifact.

### What success looks like

You should receive a Telegram summary containing project ID, tier, budget, current gate, and next expected action.

## Approving a gate

### Interaction pattern

Each approval request should include:

- Project ID.
- Gate name.
- Artifact summary.
- Risk summary.
- Cost so far.
- Idempotency key.
- Buttons: `Approve`, `Request edits`, `Reject`, `Escalate discussion`.

### Approval rules

1. Approve only if the artifact is good enough for the next phase.
2. Request edits if the direction is right but incomplete.
3. Reject if the artifact violates the project goal, budget, or safety boundary.
4. Escalate discussion if the reviewers disagree in a way you do not understand.

### Irreversible operations

Always require explicit approval for:

- Deleting databases.
- Deleting or rewriting large file trees.
- Rotating credentials.
- Publishing packages.
- Sending external messages as the user.
- Running account actions against financial, legal, medical, or identity systems.
- Force-pushing Git history.

This rule is motivated by the Replit and Gemini CLI incidents described in the Research Validation Report.

## Inspecting state

### Filesystem locations

```text
~/talisman/config/config.yaml          main non-secret configuration
~/talisman/state/TalisMan.sqlite3      SQLite state, lessons, gates, scheduler, costs
~/talisman/projects/<project-id>/      project artifacts and state
~/talisman/retros/<project-id>.md      approved retrospective documents
~/talisman/logs/                       local log files if file logging is enabled
~/talisman/secrets/                    local secret files; never commit to Git
```

### Useful commands

```bash
sqlite3 ~/talisman/state/TalisMan.sqlite3 ".tables"
sqlite3 ~/talisman/state/TalisMan.sqlite3 "SELECT project_id, name, status FROM projects;"
sqlite3 ~/talisman/state/TalisMan.sqlite3 "SELECT lesson_id, severity, statement FROM lessons WHERE status='active';"
journalctl --user -u TalisMan -n 100 --no-pager
journalctl --user -u TalisMan-gateway -n 100 --no-pager
```

## Cost monitoring

### Telegram

Send:

```text
/costs
```

Expected output:

```text
Today: $X.XX / $10.00 hard cap
Month: $Y.YY / $60.00 hard cap
Highest-cost project: <project-id>
Anomaly status: normal
```

### SQLite

```bash
sqlite3 ~/talisman/state/TalisMan.sqlite3 "SELECT provider, model, SUM(cost_usd) FROM budget_events GROUP BY provider, model;"
```

### What to do at thresholds

- Soft daily cap at `$5`: review active projects but allow work to continue.
- Hard daily cap at `$10`: TalisMan pauses API-spending work until manual override.
- Hard monthly cap at `$60`: TalisMan pauses all API-spending work until rollover or manual override.
- Anomaly trigger: if spend rate exceeds `3x` trailing-hour average in a 15-minute window, pause and inspect logs.

## Incident response

### Catastrophic-error recovery

Use this when TalisMan reports a catastrophic error or you see unexpected destructive behavior.

1. Stop services.

   ```bash
   systemctl --user stop TalisMan
   systemctl --user stop TalisMan-gateway
   ```

2. Snapshot current state before changing anything.

   ```bash
   cd ~/talisman
   tar -czf ~/talisman-incident-$(date +%Y%m%d-%H%M%S).tar.gz config state projects retros logs
   ```

3. Inspect logs.

   ```bash
   journalctl --user -u TalisMan -n 300 --no-pager > ~/talisman/logs/incident-TalisMan.log
   journalctl --user -u TalisMan-gateway -n 300 --no-pager > ~/talisman/logs/incident-gateway.log
   ```

4. Do not restart until you know whether the failure was budget, credentials, filesystem, network, or model behavior.

### Container rebuild

```bash
cd ~/talisman
podman-compose down
podman-compose build --no-cache
podman-compose up -d
```

If using Docker Compose:

```bash
cd ~/talisman
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Credential rotation

1. Stop TalisMan.

   ```bash
   systemctl --user stop TalisMan
   ```

2. Rotate the credential at the provider or Telegram source.
3. Replace the corresponding file in `~/talisman/secrets/`.
4. Fix permissions.

   ```bash
   chmod 600 ~/talisman/secrets/*.secret
   ```

5. Restart gateway and TalisMan.

   ```bash
   systemctl --user restart TalisMan-gateway
   systemctl --user start TalisMan
   ```

6. Send `/status` in Telegram.

### Backup and restore

#### Backup

```bash
cd ~/talisman
tar -czf ~/talisman-backup-$(date +%Y%m%d).tar.gz config state projects retros templates
```

#### Restore

```bash
cd ~
tar -xzf ~/talisman-backup-YYYYMMDD.tar.gz
sqlite3 ~/talisman/state/TalisMan.sqlite3 "PRAGMA integrity_check;"
```

## Maintenance tasks

### Daily

- Check `/status` and `/costs` if TalisMan is active.
- Review unresolved approval gates.

### Weekly

- Run deterministic checks.

  ```bash
  cd ~/talisman
  . .venv/bin/activate
  pre-commit run --all-files
  pytest -q
  deactivate
  ```

- Commit configuration changes.

  ```bash
  cd ~/talisman
  git status
  git add config templates src
  git commit -m "Update TalisMan configuration" || true
  ```

### Monthly

- Review budget history.
- Archive completed projects.
- Review lessons marked `active` for correctness.
- Check worker CLI versions and update pins intentionally.

### Quarterly

- Revisit sandbox hardening: rootless Podman, gVisor, or Kata Containers.
- Decide whether Model Context Protocol (MCP) read-only state exposure is justified.
- Decide whether semantic lesson retrieval is needed.

## Common failures and fixes

| Failure | Diagnosis | Fix |
|---|---|---|
| Telegram bot ignores you | User ID is not allowlisted | Update `telegram_user_allowlist.secret`, restart service |
| Telegram says unauthorized | Bot token is wrong or revoked | Rotate token through BotFather and update secret file |
| Gateway returns 401 | Shared secret mismatch | Ensure orchestrator and gateway read the same `gateway_shared_secret.secret` |
| Gateway returns 402 | Budget cap blocked the call | Inspect `/costs`, then override only if intentional |
| Worker CLI not found | `claude` or `codex` not on `PATH` | Install CLI or update service environment |
| Repeated 429 errors | Provider rate limit | Let jittered backoff run; do not override repeatedly |
| SQLite database locked | Another process holds a write transaction | Stop services, retry, inspect long-running process |
| Project waits too long | Scheduler starvation or budget pause | Check queue metrics; aging should promote after 24 hours |
| LLM review is noisy | Same-family or cross-family reviewer over-nitting | Classify slice as routine and skip same-family review if allowed |
| Container cannot reach required site | Egress allowlist too strict | Add the domain to `squid.conf`, rebuild/restart proxy, document why |

## Emergency stop

Use this if you are unsure what TalisMan is doing.

```bash
systemctl --user stop TalisMan
systemctl --user stop TalisMan-gateway
podman-compose -f ~/talisman/docker-compose.yml down || true
docker compose -f ~/talisman/docker-compose.yml down || true
```

Then inspect logs before restarting.


## Tracking TalisMan self-improvement work

Use `docs/progress/progress-ledger.md` as the single work-progress source of truth.

Each implementation slice must record:

1. Slice identifier and title.
2. Phase from the master build roadmap.
3. Lead agent and review agent.
4. Files changed.
5. Deterministic checks run.
6. Architecture-boundary checks run.
7. Cross-vendor review artifact path.
8. User decision or next required decision.
9. Open risks.
10. Next action.

A slice is not complete if the progress ledger is stale, even when the code appears to work.
