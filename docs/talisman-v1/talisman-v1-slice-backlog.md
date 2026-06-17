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
| S00.01 | 0 | Create repository skeleton | Claude Code | Codex CLI | not_started | Required folders, `AGENTS.md`, `CLAUDE.md`, and `pyproject.toml` exist. |
| S00.02 | 0 | Add import-boundary contracts | Codex CLI | Claude Code | not_started | `.importlinter` exists and `lint-imports` passes. |
| S00.03 | 0 | Add progress and review directories | Claude Code | Codex CLI | not_started | `docs/progress`, `docs/reviews`, and `docs/adr` exist with templates. |
| S01.01 | 1 | Install local development environment | Codex CLI | Claude Code | not_started | `.venv` created and all deterministic checks execute. |
| S02.01 | 2 | Implement domain models | Claude Code | Codex CLI | not_started | `Project`, `Gate`, `Artifact`, and `ReviewResult` models exist with tests. |
| S02.02 | 2 | Implement ports | Codex CLI | Claude Code | not_started | Worker, approval, state, gateway, memory, and notifier ports exist. |
| S03.01 | 3 | Implement LangGraph spiral state | Claude Code | Codex CLI | not_started | Serializable state schema and basic graph compile. |
| S03.02 | 3 | Add approval interrupt and resume | Codex CLI | Claude Code | not_started | Fake approval gate pauses and resumes after decision. |
| S04.01 | 4 | Add SQLite migrations | Claude Code | Codex CLI | not_started | Database initializes idempotently. |
| S04.02 | 4 | Add project event log | Codex CLI | Claude Code | not_started | Events persist and can be queried by project. |
| S05.01 | 5 | Add Telegram allowlist | Claude Code | Codex CLI | not_started | Non-allowlisted user is rejected. |
| S05.02 | 5 | Add approval idempotency | Codex CLI | Claude Code | not_started | Duplicate approval messages do not double-advance state. |
| S06.01 | 6 | Add Claude Code worker adapter | Claude Code | Codex CLI | not_started | Adapter passes worker contract tests. |
| S07.01 | 7 | Add Codex CLI worker adapter | Codex CLI | Claude Code | not_started | Adapter passes worker contract tests. |
| S08.01 | 8 | Add structured review artifact format | Claude Code | Codex CLI | not_started | Reviews save status, findings, and required fixes. |
| S08.02 | 8 | Enforce cross-family review before acceptance | Codex CLI | Claude Code | not_started | Slice cannot close without review artifact. |
| S09.01 | 9 | Add gateway adapter | Claude Code | Codex CLI | not_started | Model calls route through gateway port. |
| S09.02 | 9 | Add budget circuit breakers | Codex CLI | Claude Code | not_started | Simulated daily/monthly cap pauses work. |
| S10.01 | 10 | Add credential proxy | Claude Code | Codex CLI | not_started | Worker environment lacks raw provider keys. |
| S10.02 | 10 | Add egress allowlist | Codex CLI | Claude Code | not_started | Disallowed domain access fails in test profile. |
| S11.01 | 11 | Add portfolio scheduler | Claude Code | Codex CLI | not_started | Active worker slots cap is enforced. |
| S11.02 | 11 | Add wait-time aging metrics | Codex CLI | Claude Code | not_started | Wait time tracked per project. |
| S12.01 | 12 | Add health check and logs | Claude Code | Codex CLI | not_started | `/status` and log files expose health. |
| S13.01 | 13 | Add systemd units | Codex CLI | Claude Code | not_started | Services install and restart locally. |
| S14.01 | 14 | Run bootstrap self-improvement project | Claude Code | Codex CLI | not_started | TalisMan plans v1.1 improvements through gates. |
| S15.01 | 15 | Execute acceptance test plan | Codex CLI | Claude Code | not_started | Release checklist passes or has explicit waivers. |

## Slice rule

If a slice needs more than one reviewable diff, split it. Small slices preserve momentum and make inter-agent review meaningful.
