# TalisMan v1 Progress Ledger

The single source of truth for implementation progress. Updated after every slice.
Reference templates and immutable architecture artifacts live in `docs/talisman-v1/`.

## Current status summary

- **Overall status:** in_progress
- **Current phase:** Phase 8 — Inter-agent review protocol
- **Current slice:** S08.01 Structured review artifact format — review_ready (PR open; Codex review: accept)
- **Last completed slice:** S07.01 Codex CLI worker adapter (merged, PR #13) — Phase 7 complete
- **Current blocker:** awaiting human review + merge of the S08.01 PR.
- **Next human decision needed:** merge the S08.01 PR; then S08.02 (enforce cross-family review before
  acceptance — Codex lead / Claude review), which completes Phase 8.

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
| 2 | Domain and ports | accepted | 2026-06-17 | 2026-06-17 |  |
| 3 | LangGraph workflow skeleton | accepted | 2026-06-17 | 2026-06-17 |  |
| 4 | SQLite state and memory | accepted | 2026-06-17 | 2026-06-17 |  |
| 5 | Telegram approval interface | accepted | 2026-06-17 | 2026-06-17 |  |
| 6 | Claude Code worker adapter | accepted | 2026-06-17 | 2026-06-17 |  |
| 7 | Codex CLI worker adapter | accepted | 2026-06-17 | 2026-06-17 |  |
| 8 | Inter-agent review protocol | in_progress | 2026-06-17 |  |  |
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
| 2026-06-17 | S02.03 | 2 | Claude Code | Codex CLI | accepted | all five pass; negative test confirms the new contract bites | `docs/reviews/S02.03.yaml` (approve) | none | merged (PR #3) |
| 2026-06-17 | S03.01 | 3 | Claude Code | Codex CLI | accepted | all five pass; graph compiles + walks lightweight (5) and full-spiral (9) to END | `docs/reviews/S03.01.yaml` (approve) | one narrow mypy ignore for langgraph add_node overload | merged (PR #5) |
| 2026-06-17 | S03.02 | 3 | Codex CLI | Claude Code | accepted | all five pass; 17 tests incl. gate pause + 4 resume routes (approve/revise/pause/reject) on MemorySaver | `docs/reviews/S03.02.yaml` (approve) | AT-04 durable resume deferred to Phase 4 (SqliteSaver, same interface) | merged (PR #6) |
| 2026-06-17 | S04.01 | 4 | Claude Code | Codex CLI | accepted | all five pass; 19 tests (tables created + idempotent re-init preserves data) | `docs/reviews/S04.01.yaml` (pass) | SQLite placed in adapters/ (confirmed correct by reviewer) | merged (PR #7) |
| 2026-06-17 | S04.02 | 4 | Codex CLI | Claude Code | accepted | all five pass; 22 tests (cross-connection persistence, per-project isolation, stable ordering) | `docs/reviews/S04.02.yaml` (pass) | EventLog has no port yet — add one before the first core consumer (review finding) | merged (PR #8) |
| 2026-06-17 | S05.01 | 5 | Claude Code | Codex CLI | accepted | all five pass; 26 tests (allowlisted accepted, non-allowlisted rejected, fail-closed, loader) | `docs/reviews/S05.01.yaml` (accept) | none | merged (PR #9) |
| 2026-06-17 | S05.02 | 5 | Codex CLI | Claude Code | accepted | all five pass; 29 tests; INSERT-once dedup verified, error-code discrimination fail-safe (only UNIQUE swallowed) | `docs/reviews/S05.02.yaml` (pass) | no idempotency port yet; insert/advance not atomic — wiring slice to decide (review findings) | merged (PR #11) |
| 2026-06-17 | S06.01 | 6 | Claude Code | Codex CLI | accepted | all five pass; 32 tests; WorkerPort contract via injected runner (no real CLI); argv-list (no shell) | `docs/reviews/S06.01.yaml` (pass) | none | merged (PR #12) |
| 2026-06-17 | S07.01 | 7 | Codex CLI | Claude Code | accepted | all five pass; 35 tests; passes the SHARED worker contract; byte-faithful mirror of S06.01 (vendor argv only) | `docs/reviews/S07.01.yaml` (pass) | subprocess plumbing duplicated across workers — extract to workers/_subprocess once a 3rd lands (review finding) | merged (PR #13) |
| 2026-06-17 | S08.01 | 8 | Claude Code | Codex CLI | review_ready | all five pass; 38 tests; ReviewResult extended with Finding + pure dict round-trip; domain stays pure | `docs/reviews/S08.01.yaml` (accept) | Codex review terse (schema-drift follow-up still open) | human review + merge of PR |

## Decision log

| Date | Decision | Rationale | Artifact link |
|---|---|---|---|
| 2026-05-26 | Proceed with TalisMan Option C through governed slices. | User accepted full architecture target with LangGraph, structural modularity, and mandatory inter-agent review. | `docs/talisman-v1/talisman-v1-change-summary-for-audit.md` |
| 2026-06-17 | Build TalisMan via a Claude Code slice-runner loop: one branch+PR per slice, CI deterministic-check gate, cross-family review artifact, branch-protection human gate. | Dogfoods TalisMan's own governed workflow; maps the artifacts' gated loop onto GitHub. | This ledger; `README.md` |
| 2026-06-17 | Phases 0–1 established directly as the repository-constitution baseline rather than via PR-gated slices. | Bootstrap paradox: CI (the gate) needs pyproject/.importlinter/skeleton/toolchain to exist on `main` before any PR can be gated. Loop begins at Phase 2. | `docs/adr/0001-bootstrap-constitution.md` |
| 2026-06-17 | Corrected `.importlinter` contract key from `kind` to `type`. | Import Linter 2.x rejects `kind`; the canonical artifact scaffold was buggy. | `.importlinter`; ADR-0001 |
| 2026-06-17 | Baseline `pyproject` declares dev dependencies only; runtime deps added per-slice. | Coding standard: do not add runtime dependencies unless a slice needs them. | `pyproject.toml` |
| 2026-06-17 | Made the repository public and applied a branch ruleset on `main`. | Enforced protection/rulesets are unavailable on free private repos (HTTP 403). User chose public over upgrading to Pro or running unprotected. Ruleset requires the CI checks + a PR and blocks direct/force pushes and deletion. | this ledger; repo ruleset |
| 2026-06-17 | Approved ADR-0002 (Phase 3 LangGraph design); added `langgraph` as the first runtime dependency. | Resolves the Phase 3 spec gap (graph shape, gates→interrupt/resume, checkpointer injection, LangGraph/policy seam) before implementation; user merged the ADR PR. | `docs/adr/0002-langgraph-workflow-design.md`; PR #4 |
| 2026-06-17 | Approved ADR-0003 (approval idempotency design). | Resolves the Phase 5 / S05.02 spec gap (idempotency-key scheme, INSERT-once dedup via gate_events UNIQUE, reordering guard, 72h TTL) before implementation; user merged the ADR PR. | `docs/adr/0003-approval-idempotency.md`; PR #10 |

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
| SQLite event log (S04.02) has no consuming port yet | low | low | Add an `EventLog` port in `talisman_core.ports` before any core layer consumes the log; app wires the adapter (S04.02 review finding) | agents | open |
| Approval idempotency (S05.02) has no port; insert/advance not atomic | low | low | Add an idempotency port before a core consumer; the Telegram-wiring slice decides single-transaction vs recorded-row-as-replay-barrier (S05.02 review findings) | agents | open |
| Worker subprocess plumbing (CommandResult/runner) duplicated across claude_code + codex_cli | low | low | Extract to a shared `talisman_core.workers._subprocess` module once a third worker lands (S07.01 review finding); duplication keeps vendor adapters decoupled for now | agents | open |
