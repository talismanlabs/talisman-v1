# TalisMan v1 Master Build Roadmap

## Document control

- **Version:** 1.0 implementation-management baseline
- **Date:** 2026-05-26
- **Purpose:** Phase-level roadmap for building TalisMan v1 without architectural drift.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Large Language Model (LLM), Structured Query Language (SQL), and Architecture Decision Record (ADR) are spelled out on first use in this document.

## Build doctrine

TalisMan v1 targets the full local-first Option C architecture. The build is not a throwaway prototype. It proceeds through small, governed slices that always remain inside the final package boundaries.

Every phase ends with:

1. Deterministic checks: `ruff`, `mypy`, `pytest`, and `lint-imports`.
2. Cross-family LLM review.
3. Updated progress ledger.
4. Saved review artifact.
5. Human approval before moving to the next phase.

## Phase roadmap

| Phase | Name | Objective | Exit criterion |
|---:|---|---|---|
| 0 | Repository constitution | Establish repo, package structure, agent instructions, and architecture contracts. | Empty repository passes architecture checks. |
| 1 | Development environment | Install Python, virtual environment, dependencies, pre-commit, Docker or Podman. | Local checks run cleanly. |
| 2 | Domain and ports | Define pure domain objects and typed interfaces. | Contract tests compile and pass. |
| 3 | LangGraph workflow skeleton | Implement spiral state, graph nodes, checkpoints, interrupts, and resume model. | A fake project can pause and resume at an approval gate. |
| 4 | SQLite state and memory | Implement project state, events, lessons, retrospectives, and migrations. | State survives restart and lesson retrieval works. |
| 5 | Telegram approval interface | Implement allowlisted Telegram commands, approval idempotency, and ordering tolerance. | User can approve a paused fake project. |
| 6 | Claude Code worker adapter | Wrap Claude Code as a `WorkerPort`. | Stub project task runs and artifact is saved. |
| 7 | Codex CLI worker adapter | Wrap Codex Command Line Interface as a `WorkerPort`. | Opposite-family worker can run the same contract suite. |
| 8 | Inter-agent review protocol | Implement mandatory cross-vendor review artifacts. | A lead/reviewer slice produces structured review output. |
| 9 | Cost gateway | Implement LiteLLM or equivalent gateway, pre-call accounting, caps, and anomaly detection. | Simulated budget breach pauses execution. |
| 10 | Security profile | Implement host-side credential proxy, container runtime, environment scrubbing, and egress allowlist. | Worker cannot access raw long-lived credentials. |
| 11 | Scheduler and portfolio | Implement active slot cap, priorities, wait-time tracking, and aging policy. | Multiple fake projects schedule predictably. |
| 12 | Observability | Implement logs, health checks, state inspection, and incident dumps. | Operator can diagnose current status from files and logs. |
| 13 | systemd service | Install service, restart behavior, and gateway service. | Reboot/restart returns TalisMan to a known state. |
| 14 | Bootstrap self-improvement project | Run TalisMan's first project: plan v1.1 improvements. | TalisMan completes one governed self-improvement planning spiral. |
| 15 | v1 release candidate | Execute acceptance test plan and close blockers. | All release criteria pass or are explicitly waived by user. |

## Momentum controls

- No phase may remain open without an updated progress-ledger entry.
- No slice may exceed one coherent change set. Split large slices.
- No agent may mark its own work accepted.
- User approval is required at the end of every phase.
- Any boundary violation creates an ADR before code proceeds.
