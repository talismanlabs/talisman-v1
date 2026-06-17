# ADR-0001: Repository-constitution baseline and the bootstrap paradox

- **Status:** Proposed (pending human approval)
- **Date:** 2026-06-17
- **Deciders:** Pat (human), Claude Code (lead, bootstrap)
- **Related:** `docs/master-build-roadmap` (Phase 0–1), `docs/agent-coding-protocol.md`,
  guardrail #9 (no silent architecture changes — boundary/process changes require an ADR)

## Context

The TalisMan build process (master build roadmap + agent coding protocol) requires every slice to
pass through a gated loop: implement → deterministic checks (`ruff`, `mypy`, `pytest`, `lint-imports`)
→ cross-family review → ledger update → human approval. We implement those gates on GitHub as
**one branch + one PR per slice**, with a CI workflow running the deterministic checks as required
status checks and branch protection requiring an approving review.

This creates a **bootstrap paradox** for Phase 0 (repository constitution) and Phase 1 (development
environment): the CI gate cannot run the deterministic checks on a pull request until the files those
checks operate on already exist on `main` — `pyproject.toml`, `.importlinter`, the `src/talisman_core`
package skeleton, the test harness, `scripts/checks.sh`, and the CI workflow itself. You cannot
PR-gate the very machinery that performs the gating.

The original ChatGPT kickoff prompt also framed Phase 0 as work the lead agent performs directly
before the first review, which is consistent with treating it as a baseline.

## Decision

Phases 0 and 1 are established **directly as the initial `main` commit (the "repository
constitution")**, not as PR-gated slices. Specifically, the constitution baseline includes:

- the `src/talisman_core` package skeleton (eleven layer packages, docstring placeholders only);
- `pyproject.toml` (dev dependencies only; runtime deps deferred per-slice), `.importlinter`,
  `.pre-commit-config.yaml`, `.gitignore`;
- the test harness and `scripts/checks.sh` (all five checks pass green);
- the governance scaffold (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, living governance
  docs, ledger, review/ADR directories);
- the slice-runner harness (`.claude/skills/run-next-slice`, the Codex review wrapper) and CI
  (`.github/workflows/checks.yml`, `secret-scan.yml`).

The corresponding backlog slices **S00.01, S00.02, S00.03, and S01.01** are recorded in the progress
ledger as `accepted (constitution baseline)` with this ADR as their provenance.

The **autonomous slice-runner loop begins at Phase 2 (S02.01, Implement domain models)**, which is
well-specified, low-risk, and exercises both cross-family review directions across S02.01 (Claude
lead / Codex review) and S02.02 (Codex lead / Claude review).

The human-approval gate for the constitution itself is the user's review and approval of this baseline
(and this ADR), plus enabling branch protection on `main` so that all subsequent work is PR-gated.

## Consequences

- **Positive:** `main` is green and protectable from commit one; the gating machinery exists before it
  is needed; the first PR-gated slice (S02.01) produces real, reviewable domain code rather than
  scaffolding that fights the CI ordering.
- **Negative / deviation:** This deviates from the approved plan's wording, which described running
  S00.01–03 as individual PRs. The deviation is bounded to Phases 0–1, recorded here and in the
  ledger, and does not change any architecture boundary.
- **Follow-up corrections captured during bootstrap:**
  - The canonical `.importlinter` in `talisman-v1-config-templates.md` used `kind = forbidden`;
    Import Linter 2.x requires `type = forbidden`. Corrected in the live `.importlinter`.
  - Baseline `pyproject` declares only dev dependencies; runtime dependencies (langgraph, fastapi,
    httpx, pydantic, pyyaml, uvicorn) are introduced by the slices that first require them.

## Alternatives considered

1. **Run S00.01–03 as PRs with CI disabled until they merge.** Rejected: produces a window where the
   gate is off precisely while foundational files land — the opposite of the safety the gate provides.
2. **Commit an empty `main`, then PR everything including CI.** Rejected: branch protection and
   required status checks cannot be defined against checks that do not yet exist on `main`; creates a
   chicken-and-egg with required-check names and a misleading "first PR is unprotected" state.
