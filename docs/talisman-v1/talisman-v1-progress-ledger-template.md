# TalisMan v1 Progress Ledger Template

## Document control

- **Version:** 1.0 implementation-management baseline
- **Date:** 2026-05-26
- **Purpose:** Template for tracking TalisMan v1 implementation progress over time.
- **Acronym discipline:** Command Line Interface (CLI), Large Language Model (LLM), and Architecture Decision Record (ADR) are spelled out on first use in this document.

## How to use this ledger

Copy this file to `docs/progress/progress-ledger.md` in the implementation repository. Update it after every implementation slice. The ledger is the single source of truth for progress.

## Current status summary

- **Overall status:** not_started
- **Current phase:** Phase 0 Repository constitution
- **Current slice:** S00.01 Create repository skeleton
- **Last completed slice:** none
- **Current blocker:** none
- **Next human decision needed:** approve start of Phase 0

## Phase checklist

| Phase | Name | Status | Start date | Completed date | User approval |
|---:|---|---|---|---|---|
| 0 | Repository constitution | not_started |  |  |  |
| 1 | Development environment | not_started |  |  |  |
| 2 | Domain and ports | not_started |  |  |  |
| 3 | LangGraph workflow skeleton | not_started |  |  |  |
| 4 | SQLite state and memory | not_started |  |  |  |
| 5 | Telegram approval interface | not_started |  |  |  |
| 6 | Claude Code worker adapter | not_started |  |  |  |
| 7 | Codex CLI worker adapter | not_started |  |  |  |
| 8 | Inter-agent review protocol | not_started |  |  |  |
| 9 | Cost gateway | not_started |  |  |  |
| 10 | Security profile | not_started |  |  |  |
| 11 | Scheduler and portfolio | not_started |  |  |  |
| 12 | Observability | not_started |  |  |  |
| 13 | systemd service | not_started |  |  |  |
| 14 | Bootstrap self-improvement project | not_started |  |  |  |
| 15 | v1 release candidate | not_started |  |  |  |

## Slice ledger

| Date | Slice | Phase | Lead agent | Review agent | Status | Checks run | Review artifact | Open risks | Next action |
|---|---|---:|---|---|---|---|---|---|---|
|  | S00.01 | 0 |  |  | not_started |  |  |  |  |

## Decision log

| Date | Decision | Rationale | Artifact link |
|---|---|---|---|
| 2026-05-26 | Proceed with TalisMan Option C through governed slices. | User accepted full architecture target with LangGraph, structural modularity, and mandatory inter-agent review. | `talisman-v1-change-summary-for-audit.md` |

## Risk register

| Risk | Probability | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|
| Architecture drift from LLM-generated code | medium | high | Import Linter, typed ports, contract tests, cross-family review | Pat / agents | open |
| Scope creep before first full run | medium | high | Slice backlog and phase gates | Pat | open |
| Cost overrun during agentic implementation | medium | medium | Gateway caps and progress-based review | Pat | open |
