# AGENTS.md — instructions for every coding agent (Claude Code, Codex CLI, and future LLMs)

These rules apply to **any** LLM coding agent working in this repository. They are vendor-neutral;
Claude Code has an additional `CLAUDE.md`. The core rule: **agents may write code; agents may not
silently change architecture.**

## Non-negotiable architecture rules

1. Do not bypass ports. Core workflow code talks to `talisman_core.ports`, not concrete vendors.
2. Do not import adapters or workers from `domain`, `workflow`, or `policies`
   (enforced mechanically by Import Linter — see `.importlinter`).
3. Do not place business rules inside Telegram, SQLite, gateway, Claude Code, or Codex adapters.
4. Do not store secrets in source files, `.env`, configuration YAML, logs, tests, or prompts.
5. Do not perform irreversible actions without an explicit approval gate.
6. Do not mark a slice complete without `ruff`, `ruff format`, `mypy`, `pytest`, and `lint-imports`
   passing (run `./scripts/checks.sh`).
7. Do not mark a slice complete without an **opposite-family** review saved under `docs/reviews/`.
8. Do not implement more than one slice before a human merge; do not perform broad rewrites unless the
   active slice explicitly calls for one.
9. Any architecture-boundary exception — or any **under-specified slice** — requires a proposed
   Architecture Decision Record (`docs/adr/`) and a halt for human direction. Never guess.

## The slice workflow (summary)

Read the active slice in `docs/slice-backlog.md`, read this file + `docs/architecture-guardrails.md`,
state intended files, implement the smallest coherent change, run the deterministic checks, produce a
concise implementation note, hand off to the opposite-family reviewer, save the review artifact in
`docs/reviews/`, update `docs/progress/progress-ledger.md`, and stop for human approval at gates. Full
detail: `docs/agent-coding-protocol.md` and the `run-next-slice` skill.

## Required slice completion record

Every slice updates `docs/progress/progress-ledger.md` with: slice id, lead agent, review agent,
checks run, architecture-boundary result, artifacts changed, open risks, and next action.
