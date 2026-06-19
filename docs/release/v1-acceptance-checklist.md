# TalisMan v1 acceptance checklist

_Produced by slice S15.01 against the AT-01..AT-20 acceptance test plan._

**Summary:** 10 pass · 5 live-pending (operator walkthrough) · 5 waived to v1.1.

| Test | Area | Status | Evidence |
|---|---|---|---|
| AT-01 | Architecture | pass | lint-imports: 5 contracts kept, 0 broken (CI). |
| AT-02 | Static checks | pass | ruff check + mypy --strict pass on every PR (CI). |
| AT-03 | Unit tests | pass | pytest: 96+ tests pass (CI). |
| AT-04 | LangGraph pause/resume | waived | In-process gate interrupt/resume verified (workflow tests + S14.02); cross-process resume uses an in-memory MemorySaver. |
| AT-05 | Telegram allowlist | live_pending | Allowlist policy built + unit-tested (adapters/telegram/allowlist.py). Live rejection of a non-allowlisted account pending the running bot (walkthrough). |
| AT-06 | Approval idempotency | pass | SQLiteApprovalIdempotency: a repeated key advances state once (INSERT-once dedup); unit-tested (ADR-0003). |
| AT-07 | Claude Code worker | live_pending | workers/claude_code.py implements WorkerPort; unit-tested. Live controlled-slice run (transcript/artifacts saved) pending (walkthrough). |
| AT-08 | Codex CLI worker | live_pending | workers/codex_cli.py implements WorkerPort; unit-tested. Strong practical evidence: Codex CLI ran all 14 cross-family reviews this build. Live controlled-slice run via the adapter pending (walkthrough). |
| AT-09 | Cross-family review | pass | 24 structured review artifacts saved in docs/reviews/ (every slice reviewed by the opposite family). |
| AT-10 | Budget cap | pass | SQLiteBudgetAdapter pauses (BudgetCircuitOpen) when a simulated spend would breach the daily/monthly hard cap; unit-tested (ADR-0004). |
| AT-11 | Gateway pre-call accounting | pass | check_call runs BEFORE the provider call and blocks at the cap; unit-tested. |
| AT-12 | Retry jitter | waived | Full-jitter retry / Retry-After handling not implemented in the gateway client. |
| AT-13 | Credential isolation | pass | security/credentials scrubs long-lived provider/cloud keys from the worker environment; unit-tested (S10.01). |
| AT-14 | Egress allowlist | live_pending | Default-deny egress policy built + unit-tested incl. bypass classes (security/egress.py). Live proxy enforcement pending the squid deployment (walkthrough). |
| AT-15 | SQLite persistence | pass | Project state + event log persist in SQLite and survive reconnection; unit-tested (S04). Full service-restart confirmed in the walkthrough. |
| AT-16 | Retrospective | waived | Automated markdown retrospective generation not implemented. |
| AT-17 | Lessons retrieval | waived | Lessons retrieval/surfacing at intake not implemented (S14.03 deferred). |
| AT-18 | systemd recovery | live_pending | Unit files built; Restart=on-failure + gateway-first ordering verified, byte-match canonical (S13.01). Live kill-and-restart pending systemd install (walkthrough). |
| AT-19 | Incident dump | waived | Automated catastrophic-halt state dump not implemented. |
| AT-20 | Bootstrap project | pass | S14.02 ran the governed v1.1-planning spiral to completion through both gates; produced docs/talisman-v1.1-backlog.md. |

## Waivers

### AT-04 — LangGraph pause/resume
- **Reason:** Durable LangGraph checkpointer (SqliteSaver) not wired; only in-memory MemorySaver.
- **Risk:** A crash mid-gate loses the paused workflow checkpoint (project state in SQLite survives independently — see AT-15).
- **Compensating control:** Single supervised session in v1; gates are re-requestable; durable checkpointer is in the v1.1 backlog.
- **Approval:** Pat (pending)

### AT-12 — Retry jitter
- **Reason:** Retry-with-jitter was not built in v1.
- **Risk:** Transient provider HTTP errors are not auto-retried.
- **Compensating control:** Manual re-run; low frequency at single-session scale; in the v1.1 backlog.
- **Approval:** Pat (pending)

### AT-16 — Retrospective
- **Reason:** Retro generation was not built in v1 (the memory/ layer is empty).
- **Risk:** No automatic retrospective at project close.
- **Compensating control:** Manual retro; the lessons table exists; in the v1.1 backlog.
- **Approval:** Pat (pending)

### AT-17 — Lessons retrieval
- **Reason:** Lessons retrieval was not built in v1.
- **Risk:** Relevant lessons are not surfaced during intake.
- **Compensating control:** The lessons schema exists; retrieval is the lessons-retrieval item in the v1.1 backlog.
- **Approval:** Pat (pending)

### AT-19 — Incident dump
- **Reason:** Automated incident-dump trigger was not built in v1.
- **Risk:** No automatic state+log dump on catastrophic halt.
- **Compensating control:** The operational runbook documents a manual incident-dump procedure; automation in v1.1.
- **Approval:** Pat (pending)

