# TalisMan v1 Acceptance Test Plan

## Document control

- **Version:** 1.0 implementation-management baseline
- **Date:** 2026-05-26
- **Purpose:** Objective release criteria for accepting TalisMan v1.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Large Language Model (LLM), Structured Query Language (SQL), and Hypertext Transfer Protocol (HTTP) are spelled out on first use in this document.

## Acceptance principle

TalisMan v1 is accepted only when the system can complete a governed project loop, preserve state, enforce cost/security boundaries, and save inter-agent review evidence.

## Mandatory acceptance tests

| Test | Area | Procedure | Pass condition |
|---|---|---|---|
| AT-01 | Architecture | Run `lint-imports`. | All import contracts pass. |
| AT-02 | Static checks | Run `ruff check .` and `mypy src/talisman_core`. | No failures. |
| AT-03 | Unit tests | Run `pytest`. | All tests pass. |
| AT-04 | LangGraph pause/resume | Start fake project and pause at approval gate. Restart process. Approve gate. | Project resumes from checkpoint. |
| AT-05 | Telegram allowlist | Send command from non-allowlisted account. | Command is rejected and logged. |
| AT-06 | Approval idempotency | Send the same approval twice. | State advances once only. |
| AT-07 | Claude Code worker | Run a controlled worker slice. | Transcript and artifacts are saved. |
| AT-08 | Codex CLI worker | Run equivalent controlled worker slice. | Transcript and artifacts are saved. |
| AT-09 | Cross-family review | Lead with one family, review with the other. | Structured review artifact saved. |
| AT-10 | Budget cap | Simulate spend above hard daily cap. | TalisMan pauses and alerts user. |
| AT-11 | Gateway pre-call accounting | Attempt call without budget. | Call is blocked before provider request. |
| AT-12 | Retry jitter | Simulate retryable Hypertext Transfer Protocol (HTTP) statuses. | Retries use full jitter and honor `Retry-After`. |
| AT-13 | Credential isolation | Inspect worker environment. | Long-lived provider keys are absent. |
| AT-14 | Egress allowlist | Attempt disallowed network egress. | Request fails through proxy policy. |
| AT-15 | SQLite persistence | Create project, restart service, inspect state. | Project state and event log survive restart. |
| AT-16 | Retrospective | Complete test project. | Markdown retrospective generated. |
| AT-17 | Lessons retrieval | Add approved lesson and start related project. | Relevant lesson is surfaced during intake. |
| AT-18 | systemd recovery | Kill service process. | Service restarts and state is consistent. |
| AT-19 | Incident dump | Trigger catastrophic halt test mode. | State dump and logs are written. |
| AT-20 | Bootstrap project | Run TalisMan self-improvement planning project. | Full gated planning spiral completes. |

## Release decision

TalisMan v1 may be accepted when all mandatory tests pass. Any waiver must include: test identifier, reason for waiver, risk created, compensating control, and user approval.
