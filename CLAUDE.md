# CLAUDE.md — Claude Code instructions for the TalisMan build

This repository **implements TalisMan v1** — a local-first, approval-gated AI orchestration system —
and it is **built using TalisMan's own governed workflow** (we dogfood). Claude Code may write code,
but **may not silently change architecture**.

## Read before changing anything

1. This file and `AGENTS.md`.
2. `docs/architecture-guardrails.md` (ten non-negotiable rules).
3. `docs/agent-coding-protocol.md` (the slice workflow + required review-artifact format).
4. The active slice in `docs/slice-backlog.md` and the current state in
   `docs/progress/progress-ledger.md`.
5. Relevant `docs/adr/*` and the authoritative spec in `docs/talisman-v1/`
   (`talisman-v1-config-templates.md` holds canonical scaffolds — port them, don't reinvent).

## How work happens here: one slice at a time

Use the **`run-next-slice`** skill to advance the build. It executes exactly one slice end-to-end and
stops. The loop is the engine; the gates keep it safe.

Each slice = **one branch + one PR**, and must pass three independent gates before it is accepted:

1. **Deterministic checks** (`./scripts/checks.sh` → ruff, ruff-format, mypy, pytest, lint-imports).
   They run **first** and are authoritative; LLM review never replaces them.
2. **Cross-family review** (opposite family): Claude-lead → Codex reviews; Codex-lead → Claude
   reviews. Saved as `docs/reviews/<slice-id>.yaml`.
3. **Human approval**: the PR review + merge (enforced by branch protection on `main`).

## Hard rules (violations fail review)

- Do **not** bypass ports; core workflow talks to `talisman_core.ports`, not concrete vendors.
- Do **not** import adapters/workers from `domain`, `workflow`, or `policies` (Import Linter enforces).
- Do **not** put business rules inside adapters (Telegram, SQLite, gateway, Claude Code, Codex).
- Do **not** store secrets in code, `.env`, YAML, logs, tests, or prompts.
- Do **not** perform irreversible actions without an approval gate.
- Do **not** implement more than one slice before a human merge, or do broad rewrites unless the
  active slice explicitly calls for one.
- Do **not** mark a slice complete without green checks **and** an opposite-family review artifact.
- Any boundary exception, or any **under-specified slice**, requires a proposed **ADR** in
  `docs/adr/` and a **halt** for human direction — never guess.

## Stop and ask (halt the loop) when

A phase boundary is reached, or the slice touches architecture / credentials / budget logic /
irreversible actions / workflow gates, or the slice is under-specified. Phases 3–5 and 8–14 contain
known specification gaps — expect to halt and write ADRs there.

## Build state

Phases 0–1 are the **repository-constitution baseline** (see `docs/adr/0001-bootstrap-constitution.md`);
the autonomous slice-loop begins at **Phase 2 (S02.01)**. Cross-family review requires Codex CLI +
`OPENAI_API_KEY` (Stage A). Commands: `make setup`, `make checks`, `make fmt`.
