# Architecture Decision Records (ADRs)

ADRs capture decisions that change architecture boundaries, the build process, or any guardrail —
and decisions made when a slice is **under-specified** and the slice-runner must stop rather than
guess (per the build model in `README.md` and `docs/agent-coding-protocol.md`).

## When an ADR is required

- Any architecture-boundary exception (guardrail #9 — no silent architecture changes).
- Any change to the governed build process or deterministic-check gate.
- Any time a slice's specification is ambiguous or incomplete: write a proposed ADR describing the
  options and trade-offs, then **halt for human direction**.

## Format

Number sequentially (`NNNN-short-title.md`). Include: Status, Date, Deciders, Context, Decision,
Consequences, and Alternatives considered. Keep them short. Link the ADR from the progress ledger's
decision log.

## Index

- [ADR-0001: Repository-constitution baseline and the bootstrap paradox](0001-bootstrap-constitution.md)
- [ADR-0002: Phase 3 LangGraph spiral workflow design](0002-langgraph-workflow-design.md) — *Accepted*
- [ADR-0003: Approval idempotency design](0003-approval-idempotency.md) — *Proposed*
