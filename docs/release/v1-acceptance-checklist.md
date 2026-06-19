# TalisMan v1 acceptance checklist (release candidate)

_Produced by slice S15.01 against the AT-01..AT-20 acceptance test plan, corrected after the independent Codex cross-family review (docs/reviews/S15.01.yaml) blocked over-claimed PASS grades._

**Summary:** 5 pass · 8 component-verified (await integration + operator walkthrough) · 7 waived to v1.1.

**Not yet accepted.** Acceptance requires the operator walkthrough (to verify the component-verified items end-to-end) and the user's explicit approval of every waiver.

| Test | Area | Status | Evidence |
|---|---|---|---|
| AT-01 | Architecture | pass | lint-imports: 5 contracts kept, 0 broken (CI). |
| AT-02 | Static checks | pass | ruff check + mypy --strict pass on every PR (CI). |
| AT-03 | Unit tests | pass | pytest: 100 tests pass (CI). |
| AT-04 | LangGraph pause/resume | waived | In-process gate interrupt/resume verified (workflow tests + S14.02); but the checkpointer is in-memory MemorySaver, so resume does NOT survive a process restart. |
| AT-05 | Telegram allowlist | waived | Allowlist policy built + unit-tested (adapters/telegram/allowlist.py), but the live Telegram bot runtime (command handling + logging) is NOT built. |
| AT-06 | Approval idempotency | component_verified | SQLiteApprovalIdempotency dedups a repeated key (INSERT-once; unit-tested, ADR-0003). NOT yet wired into a live approval flow — integrated single-advance behavior unproven. |
| AT-07 | Claude Code worker | component_verified | workers/claude_code.py implements WorkerPort (unit-tested). No live controlled-slice run yet (transcript/artifacts) — pending the walkthrough. |
| AT-08 | Codex CLI worker | component_verified | workers/codex_cli.py implements WorkerPort (unit-tested). Strong practical evidence: Codex CLI ran all 15 cross-family reviews this build. No live run THROUGH the adapter yet. |
| AT-09 | Cross-family review | pass | 25 structured review artifacts in docs/reviews/ — every slice reviewed by the opposite family, incl. this S15.01 review which blocked an over-claimed release grading. |
| AT-10 | Budget cap | component_verified | SQLiteBudgetAdapter pauses (BudgetCircuitOpen) on a simulated hard-cap breach (unit-tested, ADR-0004). Not wired to a live model path or a user-alert path. |
| AT-11 | Gateway pre-call accounting | component_verified | check_call blocks at the cap before a call (unit-tested). Not integrated with a live model request path. |
| AT-12 | Retry jitter | waived | Full-jitter retry / Retry-After handling not implemented in the gateway client. |
| AT-13 | Credential isolation | component_verified | security/credentials.worker_environment scrubs long-lived keys (unit-tested, S10.01), but it is NOT wired into the worker subprocess runners — keys are not yet proven absent from a real worker environment (Codex S15.01 finding). |
| AT-14 | Egress allowlist | waived | Default-deny egress policy built + unit-tested incl. bypass classes (security/egress.py), but the enforcing proxy (squid) is NOT deployed. |
| AT-15 | SQLite persistence | component_verified | Event log + schema persist across connections (unit-tested, S04). But there is NO StatePort project-state store and no service-restart evidence (Codex S15.01 finding) — full project-state survival is unproven. |
| AT-16 | Retrospective | waived | Automated markdown retrospective generation not implemented. |
| AT-17 | Lessons retrieval | waived | Lessons retrieval/surfacing at intake not implemented (S14.03 deferred). |
| AT-18 | systemd recovery | component_verified | Unit files built; Restart=on-failure + gateway-first ordering verified, byte-match canonical (S13.01). No live kill-and-restart yet — pending systemd install (walkthrough). |
| AT-19 | Incident dump | waived | Automated catastrophic-halt state dump not implemented. |
| AT-20 | Bootstrap project | pass | S14.02 ran the governed v1.1-planning spiral to completion through both gates; produced docs/talisman-v1.1-backlog.md. |

## Waivers (await user approval)

### AT-04 — LangGraph pause/resume
- **Reason:** Durable LangGraph checkpointer (SqliteSaver) not wired; only in-memory MemorySaver.
- **Risk:** A crash mid-gate loses the paused workflow checkpoint.
- **Compensating control:** Single supervised session in v1; gates are re-requestable; durable checkpointer is in the v1.1 backlog.
- **Approval:** Pat — PENDING approval (operator walkthrough)

### AT-05 — Telegram allowlist
- **Reason:** Live Telegram bot runtime not built; only the allowlist policy exists.
- **Risk:** No running command surface to reject a non-allowlisted account against.
- **Compensating control:** The allowlist policy is ready to wire; live-telegram is in the v1.1 backlog.
- **Approval:** Pat — PENDING approval (operator walkthrough)

### AT-12 — Retry jitter
- **Reason:** Retry-with-jitter was not built in v1.
- **Risk:** Transient provider HTTP errors are not auto-retried.
- **Compensating control:** Manual re-run; low frequency at single-session scale; in the v1.1 backlog.
- **Approval:** Pat — PENDING approval (operator walkthrough)

### AT-14 — Egress allowlist
- **Reason:** Egress-enforcing proxy not deployed; only the host-side allowlist policy exists.
- **Risk:** No proxy actually blocks a disallowed egress at runtime.
- **Compensating control:** The policy is ready to wire to squid; proxy deployment is in the v1.1 backlog.
- **Approval:** Pat — PENDING approval (operator walkthrough)

### AT-16 — Retrospective
- **Reason:** Retro generation was not built in v1 (the memory/ layer is empty).
- **Risk:** No automatic retrospective at project close.
- **Compensating control:** Manual retro; the lessons table exists; in the v1.1 backlog.
- **Approval:** Pat — PENDING approval (operator walkthrough)

### AT-17 — Lessons retrieval
- **Reason:** Lessons retrieval was not built in v1.
- **Risk:** Relevant lessons are not surfaced during intake.
- **Compensating control:** The lessons schema exists; retrieval is the lessons-retrieval item in the v1.1 backlog.
- **Approval:** Pat — PENDING approval (operator walkthrough)

### AT-19 — Incident dump
- **Reason:** Automated incident-dump trigger was not built in v1.
- **Risk:** No automatic state+log dump on catastrophic halt.
- **Compensating control:** The operational runbook documents a manual incident-dump procedure; automation in v1.1.
- **Approval:** Pat — PENDING approval (operator walkthrough)

