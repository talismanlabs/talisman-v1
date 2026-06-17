# TalisMan v1 Slice Backlog

## Document control

- **Version:** 1.0 implementation-management baseline
- **Date:** 2026-05-26
- **Purpose:** Ordered implementation backlog for Large Language Model (LLM) coding agents.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Structured Query Language (SQL), and Architecture Decision Record (ADR) are spelled out on first use in this document.

## Slice status legend

- `not_started`
- `in_progress`
- `blocked`
- `review_ready`
- `accepted`
- `rejected`

## Backlog

| Slice | Phase | Title | Lead | Reviewer | Status | Acceptance criteria |
|---|---:|---|---|---|---|---|
| S00.01 | 0 | Create repository skeleton | Claude Code | Codex CLI | accepted | Required folders, `AGENTS.md`, `CLAUDE.md`, and `pyproject.toml` exist. (constitution baseline, ADR-0001) |
| S00.02 | 0 | Add import-boundary contracts | Codex CLI | Claude Code | accepted | `.importlinter` exists and `lint-imports` passes. (constitution baseline) |
| S00.03 | 0 | Add progress and review directories | Claude Code | Codex CLI | accepted | `docs/progress`, `docs/reviews`, and `docs/adr` exist with templates. (constitution baseline) |
| S01.01 | 1 | Install local development environment | Codex CLI | Claude Code | accepted | `.venv` created and all deterministic checks execute. (constitution baseline) |
| S02.01 | 2 | Implement domain models | Claude Code | Codex CLI | accepted | `Project`, `Gate`, `Artifact`, and `ReviewResult` models exist with tests. (merged PR #1) |
| S02.02 | 2 | Implement ports | Codex CLI | Claude Code | accepted | Worker, approval, state, gateway, memory, and notifier ports exist. (merged PR #2) |
| S02.03 | 2 | Harden ports import boundary | Claude Code | Codex CLI | accepted | `.importlinter` forbids `ports` importing `adapters`/`workers`; `lint-imports` passes (from S02.02 review finding R1). (merged PR #3) |
| S03.01 | 3 | Implement LangGraph spiral state | Claude Code | Codex CLI | accepted | Serializable state schema and basic graph compile. (per ADR-0002; merged PR #5) |
| S03.02 | 3 | Add approval interrupt and resume | Codex CLI | Claude Code | accepted | Fake approval gate pauses and resumes after decision. (interrupt()/Command resume; per ADR-0002; merged PR #6) |
| S04.01 | 4 | Add SQLite migrations | Claude Code | Codex CLI | accepted | Database initializes idempotently. (adapters/sqlite; canonical schema; merged PR #7) |
| S04.02 | 4 | Add project event log | Codex CLI | Claude Code | accepted | Events persist and can be queried by project. (SQLite events table + adapter; merged PR #8) |
| S05.01 | 5 | Add Telegram allowlist | Claude Code | Codex CLI | accepted | Non-allowlisted user is rejected. (adapters/telegram; fail-closed; merged PR #9) |
| S05.02 | 5 | Add approval idempotency | Codex CLI | Claude Code | accepted | Duplicate approval messages do not double-advance state. (INSERT-once via gate_events UNIQUE; per ADR-0003; merged PR #11) |
| S06.01 | 6 | Add Claude Code worker adapter | Claude Code | Codex CLI | accepted | Adapter passes worker contract tests. (workers/claude_code; injected runner; shared contract fixture; merged PR #12) |
| S07.01 | 7 | Add Codex CLI worker adapter | Codex CLI | Claude Code | accepted | Adapter passes worker contract tests. (workers/codex_cli; reuses shared contract fixture; merged PR #13) |
| S08.01 | 8 | Add structured review artifact format | Claude Code | Codex CLI | accepted | Reviews save status, findings, and required fixes. (domain Finding + ReviewResult.findings + dict round-trip; merged PR #14) |
| S08.02 | 8 | Enforce cross-family review before acceptance | Codex CLI | Claude Code | accepted | Slice cannot close without review artifact. (policies/review_enforcement; fail-closed; cross-family + accept required; merged PR #15) |
| S09.01 | 9 | Add gateway adapter | Claude Code | Codex CLI | accepted | Model calls route through gateway port. (adapters/gateway_client; injected transport + httpx; per ADR-0004; merged PR #17) |
| S09.02 | 9 | Add budget circuit breakers | Codex CLI | Claude Code | accepted | Simulated daily/monthly cap pauses work. (adapters/sqlite/budget; pre-call hard-cap breaker; budget_events; merged PR #18) |
| S10.01 | 10 | Add credential proxy | Claude Code | Codex CLI | review_ready | Worker environment lacks raw provider keys. (security/credentials env-scrub; scoped issuance is v1.1) |
| S10.02 | 10 | Add egress allowlist | Codex CLI | Claude Code | not_started | Disallowed domain access fails in test profile. |
| S11.01 | 11 | Add portfolio scheduler | Claude Code | Codex CLI | not_started | Active worker slots cap is enforced. |
| S11.02 | 11 | Add wait-time aging metrics | Codex CLI | Claude Code | not_started | Wait time tracked per project. |
| S12.01 | 12 | Add health check and logs | Claude Code | Codex CLI | not_started | `/status` and log files expose health. |
| S13.01 | 13 | Add systemd units | Codex CLI | Claude Code | not_started | Services install and restart locally. |
| S14.01 | 14 | Run bootstrap self-improvement project | Claude Code | Codex CLI | not_started | TalisMan plans v1.1 improvements through gates. |
| S15.01 | 15 | Execute acceptance test plan | Codex CLI | Claude Code | not_started | Release checklist passes or has explicit waivers. |

## Slice rule

If a slice needs more than one reviewable diff, split it. Small slices preserve momentum and make inter-agent review meaningful.
