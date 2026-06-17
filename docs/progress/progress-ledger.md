# TalisMan v1 Progress Ledger

The single source of truth for implementation progress. Updated after every slice.
Reference templates and immutable architecture artifacts live in `docs/talisman-v1/`.

## Current status summary

- **Overall status:** in_progress
- **Current phase:** Phase 2 — Domain and ports (S02.03 hardening in review; Phase 3 design ADR proposed)
- **Current slice:** S02.03 Harden ports import boundary — review_ready (PR open; Codex review: approve)
- **Last completed slice:** S02.02 Implement ports (merged, PR #2)
- **Current blocker:** awaiting human review + merge of the S02.03 PR, and human approval of ADR-0002
  (Phase 3 LangGraph design).
- **Next human decision needed:** merge the S02.03 PR; review/approve ADR-0002 so Phase 3 implementation
  (S03.01 spiral state + graph, S03.02 interrupt/resume) can begin.

## Build harness status (2026-06-17)

- Repo live: https://github.com/talismanlabs/talisman-v1 — **public** (changed from private so
  enforced branch protection is available on the free plan), `main` pushed.
- CI green on `main`: `deterministic-checks` ✓ and `gitleaks` ✓.
- Branch protection: **active via repository ruleset** on `main` — requires the `deterministic-checks`
  and `gitleaks` status checks, requires a pull request, and blocks direct pushes, force-pushes, and
  deletion. The merge gate is now mechanically enforced; the human is the merge authority.

## Phase checklist

| Phase | Name | Status | Start date | Completed date | User approval |
|---:|---|---|---|---|---|
| 0 | Repository constitution | accepted (constitution baseline) | 2026-06-17 | 2026-06-17 | pending |
| 1 | Development environment | accepted (constitution baseline) | 2026-06-17 | 2026-06-17 | pending |
| 2 | Domain and ports | in_progress | 2026-06-17 |  |  |
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
| 2026-06-17 | S00.01 | 0 | Claude Code (constitution) | pending human | accepted (baseline) | ruff, ruff-format, mypy, pytest, lint-imports — all pass | n/a (ADR-0001) | Phase 0 done directly, not via PR loop (bootstrap paradox) | — |
| 2026-06-17 | S00.02 | 0 | Claude Code (constitution) | pending human | accepted (baseline) | lint-imports passes (4 contracts kept) | n/a (ADR-0001) | Fixed artifact bug: `.importlinter` used `kind`; Import Linter requires `type` | — |
| 2026-06-17 | S00.03 | 0 | Claude Code (constitution) | pending human | accepted (baseline) | n/a | n/a (ADR-0001) | docs/progress, docs/reviews, docs/adr created with templates | — |
| 2026-06-17 | S01.01 | 1 | Claude Code (constitution) | pending human | accepted (baseline) | all five checks execute green via `scripts/checks.sh` | n/a (ADR-0001) | dev toolchain via uv; runtime deps deferred per-slice | — |
| 2026-06-17 | S02.01 | 2 | Claude Code | Codex CLI | accepted | ruff, ruff-format, mypy, pytest, lint-imports — all pass | `docs/reviews/S02.01.yaml` (accept) | Codex enriched review YAML vs template — align template (follow-up) | merged (PR #1) |
| 2026-06-17 | S02.02 | 2 | Codex CLI | Claude Code | accepted | ruff, ruff-format, mypy, pytest, lint-imports — all pass | `docs/reviews/S02.02.yaml` (accept) | R1 addressed by S02.03 | merged (PR #2) |
| 2026-06-17 | S02.03 | 2 | Claude Code | Codex CLI | review_ready | all five pass; negative test confirms the new contract bites | `docs/reviews/S02.03.yaml` (approve) | none | human review + merge of PR |

## Decision log

| Date | Decision | Rationale | Artifact link |
|---|---|---|---|
| 2026-05-26 | Proceed with TalisMan Option C through governed slices. | User accepted full architecture target with LangGraph, structural modularity, and mandatory inter-agent review. | `docs/talisman-v1/talisman-v1-change-summary-for-audit.md` |
| 2026-06-17 | Build TalisMan via a Claude Code slice-runner loop: one branch+PR per slice, CI deterministic-check gate, cross-family review artifact, branch-protection human gate. | Dogfoods TalisMan's own governed workflow; maps the artifacts' gated loop onto GitHub. | This ledger; `README.md` |
| 2026-06-17 | Phases 0–1 established directly as the repository-constitution baseline rather than via PR-gated slices. | Bootstrap paradox: CI (the gate) needs pyproject/.importlinter/skeleton/toolchain to exist on `main` before any PR can be gated. Loop begins at Phase 2. | `docs/adr/0001-bootstrap-constitution.md` |
| 2026-06-17 | Corrected `.importlinter` contract key from `kind` to `type`. | Import Linter 2.x rejects `kind`; the canonical artifact scaffold was buggy. | `.importlinter`; ADR-0001 |
| 2026-06-17 | Baseline `pyproject` declares dev dependencies only; runtime deps added per-slice. | Coding standard: do not add runtime dependencies unless a slice needs them. | `pyproject.toml` |
| 2026-06-17 | Made the repository public and applied a branch ruleset on `main`. | Enforced protection/rulesets are unavailable on free private repos (HTTP 403). User chose public over upgrading to Pro or running unprotected. Ruleset requires the CI checks + a PR and blocks direct/force pushes and deletion. | this ledger; repo ruleset |

## Risk register

| Risk | Probability | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|
| Architecture drift from LLM-generated code | medium | high | Import Linter, typed ports, contract tests, cross-family review, CI gate | Pat / agents | open |
| Scope creep before first full run | medium | high | Slice backlog, phase gates, one-PR-per-slice rule | Pat | open |
| Cost overrun during agentic implementation | medium | medium | Watch usage; per-slice diffs; (Phase 9 gateway does not govern bootstrap spend) | Pat | open |
| Under-specified slices (Phases 3–5, 8–14) cause agent drift | high | medium | Slice-runner halts and writes a proposed ADR instead of guessing | agents | open |
| Codex CLI headless implementation unreliable/costly | medium | medium | Fallback (ADR): Claude implements, Codex still reviews every slice | Pat / agents | open |
| Port-layer purity enforced by review, not Import Linter | low | medium | Added `ports_do_not_import_infrastructure` Import Linter contract (S02.03); verified by negative test | agents | mitigated |
| Review-artifact YAML schema drifts between reviewers (Codex/Claude improvise keys) | low | low | Align `docs/reviews/REVIEW-TEMPLATE.yaml` + pin the schema in both review prompts (follow-up) | agents | open |
| Codex `workspace-write` sandbox blocked by bwrap (no loopback netns) in this env | low | low | Use `--sandbox danger-full-access` for Codex-led implementation; bounded by the outer environment + review + checks | agents | open |
