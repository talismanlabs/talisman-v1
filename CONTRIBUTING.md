# Contributing to TalisMan v1

TalisMan is built in small, governed slices. This guide is for humans operating or reviewing the
build. Agents follow `AGENTS.md` / `CLAUDE.md` and the `run-next-slice` skill.

## Local setup

```bash
make setup     # uv venv + dev toolchain (dev deps only; runtime deps are added per-slice)
make checks    # ruff, ruff-format, mypy, pytest, lint-imports  (the authoritative gate)
make fmt       # auto-format + auto-fix
make hooks     # optional: install pre-commit hooks
```

Requirements: Python 3.11+ and [`uv`](https://docs.astral.sh/uv/). Cross-family review additionally
requires Codex CLI on `PATH` and `OPENAI_API_KEY` set.

## The rules of the build

- **One slice = one branch = one PR.** Branch names: `slice/<id>-<slug>` (e.g. `slice/S02.01-domain-models`).
- **Deterministic checks run first** and must be green before review (`make checks`, mirrored in CI).
- **Cross-family review is mandatory:** Claude-lead slices are reviewed by Codex; Codex-lead by Claude.
  The review artifact is committed as `docs/reviews/<id>.yaml`.
- **The progress ledger is the source of truth:** `docs/progress/progress-ledger.md` is updated every slice.
- **Human approval = PR merge.** Branch protection on `main` requires green CI + one approving review.
  No agent merges its own work.
- **Secrets never enter the repo.** They are read from files at runtime (outside the tree); `.gitignore`
  and gitleaks guard against accidents.
- **Architecture is enforced, not suggested.** Import Linter contracts in `.importlinter` fail CI on
  any boundary violation. Boundary changes require an ADR (`docs/adr/`) and approval.

## Reviewing a slice PR

Confirm: CI green; `docs/reviews/<id>.yaml` present with `final_recommendation: accept`; the diff is
one coherent change matching the slice's acceptance criteria with no scope creep or boundary
violations; the ledger is updated. Then approve and merge.

## Where things live

- `docs/talisman-v1/` — immutable architecture reference (the spec).
- `docs/architecture-guardrails.md`, `docs/agent-coding-protocol.md`, `docs/slice-backlog.md` — living
  governance.
- `docs/progress/`, `docs/reviews/`, `docs/adr/` — progress, reviews, decisions.
- `src/talisman_core/` — the orchestrator's layered packages.
- `scripts/`, `Makefile`, `.claude/skills/` — the build harness.
