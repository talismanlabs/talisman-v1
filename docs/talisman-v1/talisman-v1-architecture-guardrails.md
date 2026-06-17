# TalisMan v1 Architecture Guardrails

## Document control

- **Version:** 1.0 implementation-management baseline
- **Date:** 2026-05-26
- **Purpose:** Non-negotiable architecture rules for implementation and future self-improvement.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Large Language Model (LLM), Structured Query Language (SQL), and Architecture Decision Record (ADR) are spelled out on first use in this document.

## Guardrail summary

TalisMan must remain a modular, auditable, local-first project orchestration system. It must not become a pile of scripts, a single-vendor agent, or an uncontrolled autonomous process.

## Non-negotiable rules

1. **Ports before adapters.** Core workflow code depends on typed ports, not concrete external systems.
2. **LangGraph owns workflow mechanics only.** TalisMan owns policy, security, review, and cost decisions.
3. **Domain remains pure.** Domain objects do not import infrastructure, adapters, workers, or application wiring.
4. **Cross-family review is mandatory.** No implementation slice is accepted without opposite-family review.
5. **Deterministic checks run first.** LLM review never replaces `ruff`, `mypy`, `pytest`, or `lint-imports`.
6. **Credentials stay out of workers.** Workers receive scoped access through the host-side proxy, not raw long-lived credentials.
7. **Irreversible actions require gates.** Destructive, financial, publishing, credential, or external-account actions require explicit approval.
8. **State is auditable.** Project state, approvals, reviews, costs, and incidents are recorded in SQLite, markdown, or logs.
9. **No silent architecture changes.** Boundary changes require an Architecture Decision Record (ADR) and user approval.
10. **Self-improvement is governed.** TalisMan may help improve itself only through the same gated workflow it applies to other projects.

## Required checks

```bash
ruff check .
mypy src/talisman_core
pytest
lint-imports
```

## Boundary violation response

If an agent believes a boundary must be violated:

1. Stop implementation.
2. Write a proposed ADR in `docs/adr/`.
3. Explain the trade-off.
4. Request cross-family review.
5. Wait for user approval before proceeding.
