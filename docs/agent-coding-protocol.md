# TalisMan v1 Agent Coding Protocol

## Document control

- **Version:** 1.0 implementation-management baseline
- **Date:** 2026-05-26
- **Purpose:** Working rules for Claude Code, Codex Command Line Interface (CLI), and any future Large Language Model (LLM) coding agents.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Large Language Model (LLM), and Architecture Decision Record (ADR) are spelled out on first use in this document.

## Core rule

Agents may write code. Agents may not silently change architecture.

## Required slice workflow

1. Read the active slice from `docs/slice-backlog.md`.
2. Read `AGENTS.md`, `CLAUDE.md`, and `docs/architecture-guardrails.md`.
3. State the intended files to change.
4. Implement the smallest coherent change.
5. Run deterministic checks:

```bash
ruff check .
mypy src/talisman_core
pytest
lint-imports
```

6. Produce a concise implementation note.
7. Hand off to the opposite-family reviewer.
8. Save the review artifact in `docs/reviews/`.
9. Update `docs/progress/progress-ledger.md`.
10. Stop for user approval if the slice touches architecture, credentials, budget logic, irreversible actions, or workflow gates.

## Lead/reviewer assignment

- If Claude Code leads, Codex CLI reviews.
- If Codex CLI leads, Claude Code reviews.
- Same-family review may be added for critical slices, but it does not replace cross-family review.

## Required review artifact format

```yaml
slice_id: S00.00
lead_agent: claude_code_or_codex_cli
review_agent: codex_cli_or_claude_code
review_status: pass | pass_with_notes | block
risk_level: low | medium | high
checks_observed:
  ruff: pass | fail | not_run
  mypy: pass | fail | not_run
  pytest: pass | fail | not_run
  lint_imports: pass | fail | not_run
architecture_boundary_check: pass | fail
security_check: pass | fail | not_applicable
findings:
  - id: R1
    severity: low | medium | high | blocker
    finding: "Describe the issue."
    required_fix: "Describe the required fix or say none."
final_recommendation: accept | revise | reject
```

## Prohibited behavior

- Do not create hidden global state.
- Do not bypass ports for convenience.
- Do not put secrets in files or prompts.
- Do not replace deterministic tests with LLM review.
- Do not collapse adapters into workflow code.
- Do not mark a slice complete without review evidence.
- Do not perform broad rewrites unless the active slice explicitly calls for one.
