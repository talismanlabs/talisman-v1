# TalisMan v1

A local-first, approval-gated, auditable AI orchestration system that coordinates **Claude Code** and
**Codex CLI** through a modular, cross-vendor development workflow. This repository implements TalisMan
— and is itself **built using TalisMan's own governed slice workflow** (we dogfood the architecture).

> Umbrella concept: a *project-agnostic development environment* (PADE). TalisMan v1 is the first
> implementation.

## What this is

TalisMan runs long software projects through a gated "spiral" (interview → discovery → synthesis →
plan → red-team → slice approval → implementation → review → retro), with a human approving at the
gates via Telegram. It enforces module boundaries, routes all model calls through a budget/credential
gateway, keeps long-lived secrets out of workers, and records everything to SQLite + markdown for
audit. The full architecture and rationale live in [`docs/talisman-v1/`](docs/talisman-v1/).

## How it is built: governed slices

Implementation proceeds one small **slice** at a time. Each slice is one branch and one pull request,
and must clear three independent gates before it is accepted:

1. **Deterministic checks** — `ruff`, `ruff format`, `mypy`, `pytest`, `lint-imports`
   (run `./scripts/checks.sh`; mirrored in CI). They run first and are authoritative.
2. **Cross-family review** — the opposite vendor reviews the diff (Claude-lead → Codex; Codex-lead →
   Claude), recorded as `docs/reviews/<slice>.yaml`.
3. **Human approval** — PR review + merge, enforced by branch protection on `main`.

The engine that drives this is the **`run-next-slice`** skill: it runs exactly one slice end-to-end
and **halts** at phase boundaries, risk-gated slices, and under-specified slices (where it writes a
proposed ADR instead of guessing). This makes the build autonomous *within* well-specified, low-risk
work and human-gated everywhere it matters.

```
pick next slice ─▶ branch ─▶ implement ─▶ ./scripts/checks.sh ─▶ cross-family review
      ▲                                                                   │
      └──────────  human reviews + merges PR  ◀── open PR ◀── update ledger
```

## Quick start

```bash
make setup     # uv venv + dev toolchain
make checks    # run the full deterministic-check gate
```

Then advance the build with the `run-next-slice` skill (optionally under `/loop` for self-paced runs).
Cross-family review requires Codex CLI + `OPENAI_API_KEY`.

## Status

Phases 0–1 (repository constitution + dev environment) are established as the baseline
(see [`docs/adr/0001-bootstrap-constitution.md`](docs/adr/0001-bootstrap-constitution.md)). The
autonomous slice-loop begins at **Phase 2**. Track progress in
[`docs/progress/progress-ledger.md`](docs/progress/progress-ledger.md) and the
[slice backlog](docs/slice-backlog.md).

## Repository layout

| Path | What |
|---|---|
| `src/talisman_core/` | Layered orchestrator packages (domain, ports, workflow, policies, adapters, workers, memory, security, scheduler, observability, app) |
| `docs/talisman-v1/` | Immutable architecture reference (the spec) |
| `docs/architecture-guardrails.md`, `docs/agent-coding-protocol.md`, `docs/slice-backlog.md` | Living governance |
| `docs/progress/`, `docs/reviews/`, `docs/adr/` | Progress ledger, review artifacts, decision records |
| `scripts/`, `Makefile`, `.claude/skills/` | Build harness (check gate, Codex review wrapper, slice-runner) |
| `.github/workflows/` | CI deterministic-check gate + secret scan |

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the operating guide and [`AGENTS.md`](AGENTS.md) /
[`CLAUDE.md`](CLAUDE.md) for agent rules.
