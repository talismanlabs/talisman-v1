# TalisMan v1 Change Summary for Independent Audit

## Document control

- **Version:** 1.0 audit handoff
- **Date:** 2026-05-26
- **Purpose:** Portable summary of changes made after the initial artifact set, for review in a new chat or by another reviewer.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Large Language Model (LLM), and Architecture Decision Record (ADR) are spelled out on first use in this document.

## Context

The original artifact set was generated from two inputs:

1. `clawdbot-v1-architecture-decisions.pdf`, the Decision Register.
2. `Clawdbot v1 Architecture_ Multi-Agent Orchestration Validation Report.md`, the Research Validation Report.

After reviewing the first artifact set, the user approved a controlled update. This file summarizes only the changes from that acceptance-review discussion.

## User-approved changes

### 1. Rename implementation system to TalisMan

- **Before:** Working name was `clawdbot`.
- **After:** Implementation name is **TalisMan**.
- **Package convention:** Use `talisman_core` for the Python package and `~/talisman` for the local root path.
- **Audit question:** Does the rename introduce collisions or ambiguity with existing tools named Talisman?

### 2. Keep LangGraph in v1 now

- **Before:** The final architecture already recommended LangGraph, but the implementation discussion considered deferring it.
- **After:** LangGraph is mandatory in the initial implementation baseline.
- **Boundary:** LangGraph owns workflow mechanics: state machine, checkpoints, interrupts, and resume behavior. TalisMan owns policy, review, security, budget, and worker invocation.
- **Audit question:** Is the LangGraph scope narrow enough to avoid over-frameworking v1?

### 3. Two-tier workflow with user override

- **Before:** Research recommended two tiers; user had originally rejected tiering.
- **After:** User accepted two tiers if override is available.
- **Rule:** TalisMan may recommend `lightweight` or `full_spiral`, but the user can override either direction.
- **Audit question:** Are the tier triggers and overrides explicit enough in configuration and Telegram flow?

### 4. Structural modularity is mandatory

- **Before:** The architecture was modular in concept.
- **After:** Modularity is mechanically enforced with package boundaries, typed ports, Import Linter, contract tests, and agent-facing instructions.
- **Reason:** Long-term self-improvability is a core value equal in importance to inter-model review.
- **Audit question:** Are the import contracts strong enough to prevent Large Language Model (LLM)-generated architectural drift?

### 5. Inter-agent review is mandatory

- **Before:** Cross-vendor review was a core architecture feature.
- **After:** It is restated as a required implementation invariant for every meaningful slice.
- **Rule:** A lead agent cannot self-accept. Opposite-family review is required and saved as an artifact.
- **Audit question:** Are exceptions narrow, explicit, and safe?

### 6. Target Option C through governed slices

- **Before:** Conversation explored whether to build a thinner first slice.
- **After:** User leans toward and accepted building the full initial architecture, provided progress can be tracked and controlled.
- **Rule:** Do not build a disposable prototype. Build the final architecture incrementally.
- **Audit question:** Does the roadmap balance ambition with momentum and testability?

## New documents generated

1. `talisman-v1-master-build-roadmap.md`
2. `talisman-v1-slice-backlog.md`
3. `talisman-v1-agent-coding-protocol.md`
4. `talisman-v1-progress-ledger-template.md`
5. `talisman-v1-acceptance-test-plan.md`
6. `talisman-v1-architecture-guardrails.md`
7. `talisman-v1-change-summary-for-audit.md`

## Existing documents updated

1. `talisman-v1-architecture-final.md`
2. `talisman-v1-implementation-guide.md`
3. `talisman-v1-config-templates.md`
4. `talisman-v1-operational-runbook.md`
5. `talisman-v1-decision-audit.md`

## Deliberately not changed

- No change to the local-first constraint.
- No change to the Telegram v1 interface.
- No change to the $100/month baseline budget assumption.
- No change to cross-vendor diversity as a non-negotiable requirement.
- No change to SQLite as the day-one memory and state substrate.
- No change to credential isolation, host-side proxy, or egress allowlist direction.
- No change to the decision that a public web dashboard is out of scope for v1.

## Recommended audit procedure

1. Compare `talisman-v1-decision-audit.md` against the original Decision Register.
2. Confirm every accepted change above appears in at least one updated deliverable.
3. Confirm no unapproved architecture change was introduced.
4. Confirm implementation-management documents are sufficient to track work over time.
5. Confirm code scaffolding in `talisman-v1-config-templates.md` aligns with the architecture guardrails.
