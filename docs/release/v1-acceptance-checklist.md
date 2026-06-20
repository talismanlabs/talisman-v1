# TalisMan v1 acceptance checklist — ACCEPTED 2026-06-19

_Produced by slice S15.01 against the AT-01..AT-20 acceptance test plan (corrected after the independent Codex cross-family review blocked over-claimed PASS grades), then formally accepted in S15.02. Founder approval: docs/release/v1-waiver-approval-2026-06-19.md._

**Summary:** v1 ACCEPTED (2026-06-19). 6 criteria PASS end-to-end (CI/artifacts) · 9 component-verified (several also shown live in the operator walkthrough as prototype evidence; hardening tracked as v1.1-P1) · 5 waived with founder approval.

**ACCEPTED 2026-06-19** on five end-to-end PASS criteria plus the five founder-approved waivers (durable approval artifact: docs/release/v1-waiver-approval-2026-06-19.md). The operator walkthrough demonstrated several component-verified behaviours using prototype runtime code built live outside governance — recorded as prototype/operator evidence, not reviewed release proof; each flips to PASS as its v1.1-P1 code lands under governance (AT-13 was the first, via S16.03).

| Test | Area | Status | Evidence |
|---|---|---|---|
| AT-01 | Architecture | pass | lint-imports: 5 contracts kept, 0 broken (CI). |
| AT-02 | Static checks | pass | ruff check + mypy --strict pass on every PR (CI). |
| AT-03 | Unit tests | pass | pytest: 100+ tests pass (CI). |
| AT-04 | LangGraph pause/resume | waived | In-process gate interrupt/resume verified (workflow tests + S14.02); but the checkpointer is in-memory MemorySaver, so resume does NOT survive a process restart. |
| AT-05 | Telegram allowlist | component_verified | allowlist policy built + unit-tested (adapters/telegram/allowlist.py). The live @Talisman0_bot runtime accepting an allowlisted account and rejecting others was shown in the operator walkthrough. Prototype/operator evidence only (built live outside the governed slice loop, 2026-06-19; transcript: founder-audit-package/2026-06-19/walkthrough/part2-live-transcript.txt) — NOT reviewed release proof; flips to PASS when its governed v1.1-P1 code lands. (bot runtime: adapters/telegram/bot.py). |
| AT-06 | Approval idempotency | component_verified | SQLiteApprovalIdempotency dedups a repeated key (INSERT-once; unit-tested, ADR-0003). NOT yet wired into a live approval flow — integrated single-advance behavior unproven. |
| AT-07 | Claude Code worker | component_verified | workers/claude_code.py implements WorkerPort (unit-tested). A live controlled-slice run was shown in the operator walkthrough. Prototype/operator evidence only (built live outside the governed slice loop, 2026-06-19; transcript: founder-audit-package/2026-06-19/walkthrough/part2-live-transcript.txt) — NOT reviewed release proof; flips to PASS when its governed v1.1-P1 code lands. (runner wiring is v1.1-P1). |
| AT-08 | Codex CLI worker | component_verified | workers/codex_cli.py implements WorkerPort and now uses the invocation Codex CLI actually requires — prompt on stdin + --skip-git-repo-check (S16.05, unit-tested incl. a real-subprocess stdin test); Codex CLI also ran the cross-family reviews throughout this build. Flips to PASS on a live run through the adapter (real Codex, not exercisable in CI). |
| AT-09 | Cross-family review | pass | 25 structured review artifacts in docs/reviews/ — every slice reviewed by the opposite family, incl. the S15.01 review which blocked an over-claimed release grading. |
| AT-10 | Budget cap | component_verified | SQLiteBudgetAdapter pauses (BudgetCircuitOpen) on a simulated hard-cap breach (unit-tested, ADR-0004). Not wired to a live model path or a user-alert path. |
| AT-11 | Gateway pre-call accounting | component_verified | check_call blocks at the cap before a call (unit-tested). Not integrated with a live model request path. |
| AT-12 | Retry jitter | waived | Full-jitter retry / Retry-After handling not implemented in the gateway client. |
| AT-13 | Credential isolation | pass | security/credentials.worker_environment is wired (S16.03) as the single, unbypassable spawn point in workers/_subprocess.default_runner used by both worker adapters; a CI contract test spawns a REAL child process and proves ANTHROPIC_API_KEY / OPENAI_API_KEY / GITHUB_TOKEN are absent from the worker environment (D6). |
| AT-14 | Egress allowlist | component_verified | Default-deny egress policy built + unit-tested incl. bypass classes (security/egress.py). The gatekeeper CONNECT proxy — the allowlist DECISION point — is built under governance (adapters/egress_proxy.py, ADR-0006, S16.04) and integration-tested: a non-allowlisted CONNECT is refused 403 and an allowlisted target tunnels end-to-end. This is necessary but not sufficient: env-var routing (HTTPS_PROXY) is cooperative and bypassable, so AT-14 flips to PASS only once egress is ENFORCED at the OS level (network namespace / firewall) so a worker cannot reach the network except through the proxy — proven by a test that direct egress is blocked. |
| AT-15 | SQLite persistence | component_verified | Event log + schema persist across connections (unit-tested, S04); a fresh-handle restart was shown in the walkthrough. Prototype/operator evidence only (built live outside the governed slice loop, 2026-06-19; transcript: founder-audit-package/2026-06-19/walkthrough/part2-live-transcript.txt) — NOT reviewed release proof; flips to PASS when its governed v1.1-P1 code lands. A StatePort project-state store remains a v1.1 item; flips to PASS when that store lands. |
| AT-16 | Retrospective | waived | Automated markdown retrospective generation not implemented. |
| AT-17 | Lessons retrieval | waived | Lessons retrieval/surfacing at intake not implemented (S14.03 deferred). |
| AT-18 | systemd recovery | component_verified | Unit files built; Restart=on-failure + gateway-first ordering verified byte-match canonical (S13.01). A live kill -9 → auto-restart (via `--serve`) was shown in the walkthrough. Prototype/operator evidence only (built live outside the governed slice loop, 2026-06-19; transcript: founder-audit-package/2026-06-19/walkthrough/part2-live-transcript.txt) — NOT reviewed release proof; flips to PASS when its governed v1.1-P1 code lands. (the --serve service runtime is a v1.1-P1 slice). |
| AT-19 | Incident dump | waived | Automated catastrophic-halt state dump not implemented. |
| AT-20 | Bootstrap project | pass | S14.02 ran the governed v1.1-planning spiral to completion through both gates; produced docs/talisman-v1.1-backlog.md. |

## Waivers (approved by founder 2026-06-19)

### AT-04 — LangGraph pause/resume
- **Reason:** Durable LangGraph checkpointer (SqliteSaver) not wired; only in-memory MemorySaver.
- **Risk:** A crash mid-gate loses the paused workflow checkpoint.
- **Compensating control:** Single supervised session in v1; gates are re-requestable; durable checkpointer is the first v1.1 feature project.
- **Approval:** Pat (founder) — APPROVED 2026-06-19 (docs/release/v1-waiver-approval-2026-06-19.md)

### AT-12 — Retry jitter
- **Reason:** Retry-with-jitter was not built in v1.
- **Risk:** Transient provider HTTP errors are not auto-retried.
- **Compensating control:** Manual re-run; low frequency at single-session scale; in the v1.1 backlog.
- **Approval:** Pat (founder) — APPROVED 2026-06-19 (docs/release/v1-waiver-approval-2026-06-19.md)

### AT-16 — Retrospective
- **Reason:** Retro generation was not built in v1 (the memory/ layer is empty).
- **Risk:** No automatic retrospective at project close.
- **Compensating control:** Manual retro; the lessons table exists; in the v1.1 backlog.
- **Approval:** Pat (founder) — APPROVED 2026-06-19 (docs/release/v1-waiver-approval-2026-06-19.md)

### AT-17 — Lessons retrieval
- **Reason:** Lessons retrieval was not built in v1.
- **Risk:** Relevant lessons are not surfaced during intake.
- **Compensating control:** The lessons schema exists; retrieval is in the v1.1 backlog.
- **Approval:** Pat (founder) — APPROVED 2026-06-19 (docs/release/v1-waiver-approval-2026-06-19.md)

### AT-19 — Incident dump
- **Reason:** Automated incident-dump trigger was not built in v1.
- **Risk:** No automatic state+log dump on catastrophic halt.
- **Compensating control:** The operational runbook documents a manual incident-dump procedure; automation in v1.1.
- **Approval:** Pat (founder) — APPROVED 2026-06-19 (docs/release/v1-waiver-approval-2026-06-19.md)

