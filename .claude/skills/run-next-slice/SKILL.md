---
name: run-next-slice
description: Execute exactly ONE governed TalisMan implementation slice end-to-end (branch → implement → deterministic checks → cross-family review → ledger → PR), halting at phase boundaries, risk gates, and under-specified slices. Use to advance the TalisMan build, including under /loop.
---

# run-next-slice — the TalisMan governed slice-runner

Run **one** slice per invocation, then stop. This is the autonomous build engine; it is
idempotent and safe under `/loop`. Never run more than one slice's worth of change before a
human merge.

## 0. Preconditions (abort with a clear message if unmet)

- Working tree is clean and on an up-to-date `main` (`git fetch && git status`).
- `.venv` exists (`make setup` if not) and `./scripts/checks.sh` is green on `main`.
- Read `docs/progress/progress-ledger.md` to find the **current slice** and status.

**Idempotency / `/loop` safety:** if the current slice already has an open PR awaiting human
merge (check `gh pr list --head slice/<id>-* --state open`), do nothing except report
"awaiting human merge for <id>" and stop. Do not re-implement.

## 1. Select the slice and run the GATE CHECK (before any code)

From `docs/slice-backlog.md`, take the next `not_started` slice whose phase is approved in the
ledger. Then evaluate the gates — **HALT and notify the human (do not implement) if any hold**:

- **Phase boundary:** the slice begins a new phase whose start the human has not approved.
- **Risk-gated slice:** it touches architecture, credentials, budget logic, irreversible actions,
  or workflow gates (agent-coding-protocol step 10).
- **Under-specified slice (spec gap):** acceptance criteria or design are ambiguous/incomplete
  (notably Phases 3–5, 8–14). In this case **write a proposed `docs/adr/NNNN-*.md`** laying out the
  options and trade-offs, commit it on a `adr/<topic>` branch, open a PR, and halt for direction.
  **Never guess on a spec gap.**

If a gate halts you, post a concise summary of *why* and *what decision you need*, then stop.

## 2. Load context

Read `CLAUDE.md`, `AGENTS.md`, `docs/architecture-guardrails.md`, the slice's row in
`docs/slice-backlog.md`, any relevant ADRs, and the authoritative spec in
`docs/talisman-v1/` (especially `talisman-v1-config-templates.md`, which contains canonical
scaffolds to port rather than reinvent).

## 3. Branch

`git switch -c slice/<id>-<short-slug>` (e.g. `slice/S02.01-domain-models`).

## 4. State intended files

List the files you will add/change and why. Keep to the **smallest coherent change** — one
reviewable diff. If it needs more than one diff, it is two slices; split it.

## 5. Implement

- **Claude is lead** (per the backlog's Lead column): implement directly. Prefer porting the
  canonical scaffold from `docs/talisman-v1/talisman-v1-config-templates.md` faithfully.
- **Codex is lead:** drive Codex CLI headless to implement, e.g.
  `codex exec --sandbox workspace-write -` with a prompt that states the slice, its acceptance
  criteria, and the boundary rules. (If Codex headless implementation proves unreliable, invoke the
  ADR fallback: Claude implements, Codex still reviews — see ADR and ledger.)
- Add any *new* runtime dependency only if this slice needs it; update `pyproject.toml`.
- No secrets in code, tests, configs, or prompts. Ever.

## 6. Deterministic checks (must be green before review)

Run `./scripts/checks.sh`. Fix until ruff, ruff-format, mypy, pytest, and lint-imports all pass.
LLM review never substitutes for these.

## 7. Cross-family review (opposite family)

- **Claude lead → Codex reviews:** `scripts/codex_review.sh <id> main` → writes
  `docs/reviews/<id>.yaml`.
- **Codex lead → Claude reviews:** spawn an INDEPENDENT Claude reviewer (a fresh Task agent with a
  skeptical, refute-by-default brief) to evaluate the diff against the guardrails and acceptance
  criteria; write `docs/reviews/<id>.yaml` in the template format.
- If `review_status` is `block`/`revise`: address the required fixes, re-run checks, re-review.
  Only `accept` (or `pass`/`pass_with_notes`) may proceed.

## 8. Update the ledger

Append/refresh the slice row in `docs/progress/progress-ledger.md`: date, slice, phase, lead,
reviewer, status (`review_ready`), checks run, review-artifact path, open risks, next action.

## 9. Commit + open PR (the human gate)

- Commit with a message naming the slice and summarizing the change; end with the Co-Authored-By
  trailer.
- `git push -u origin HEAD` and `gh pr create` with a body that links: the slice id + acceptance
  criteria, the deterministic-check result, the review artifact, and the ledger entry.
- **Do NOT merge.** Branch protection + the human's PR approval is the acceptance gate.

## 10. Stop and report

Report: slice id, what changed, checks result, review verdict, PR URL, and whether the next slice
is auto-eligible or gated. Then stop. The human reviews and merges; the next invocation (or `/loop`
tick) continues from the updated `main`.
