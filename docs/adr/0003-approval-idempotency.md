# ADR-0003: Approval idempotency design

- **Status:** Proposed (pending human approval — resolves the Phase 5 / S05.02 spec gap before
  implementation)
- **Date:** 2026-06-17
- **Deciders:** Pat (human, approver), Claude Code (author)
- **Related:** architecture decision D3 (Telegram hardening: "every approval message includes an
  idempotency key"), `gate_events` table (`idempotency_key TEXT NOT NULL UNIQUE`, Phase 4),
  `ports/approval.py` (`ApprovalRequest.idempotency_key`), config
  (`telegram.approval_idempotency_ttl_hours: 72`, `tolerate_message_reordering: true`), slice S05.02.

## Context

S05.02 ("Duplicate approval messages do not double-advance state") is a **known specification gap**.
The artifacts give the *substrate* — a `gate_events.idempotency_key` UNIQUE column, an
`idempotency_key` field on `ApprovalRequest`, a 72-hour TTL, and a "tolerate message reordering" flag —
but **not** how the key is generated, what it identifies, how duplicate suppression actually works, how
reordering is handled, or what the TTL governs. Per the build model, the slice-runner halts on a spec
gap and proposes an ADR rather than guess. This is that ADR; approving it gives S05.02 a concrete,
reviewable target.

Why this matters (D3 / guardrail #7): an approval moves a gate, which can authorize irreversible work.
A duplicated, replayed, or reordered approval must never advance a gate twice or advance the wrong
gate. Duplicate suppression must live in **durable state**, not agent memory — a buggy or
prompt-injected agent must be unable to double-apply (the same principle as budget enforcement).

## Decision (proposed)

### 1. Idempotency key — generated per approval *request*, carried by the message

When the orchestrator issues an approval request for a specific pending gate, it generates a unique
key and embeds it in the Telegram approval control (inline-button `callback_data`):

```
idempotency_key = f"{project_id}:{gate_id}:{nonce}"     # nonce = uuid4 hex, per request
```

- Duplicate **deliveries or taps of the same approval prompt** carry the **same** key → deduplicated.
- A **new** prompt for the same gate (e.g. after a `revise` re-enters the gate) gets a **new** key, so
  a later legitimate approval is a distinct event and is not suppressed by the earlier one.
- The key is opaque to the user and the Telegram adapter; only the orchestrator generates it and the
  persistence layer enforces uniqueness.

### 2. Duplicate suppression — INSERT-once against `gate_events` (durable, not agent-trusted)

Applying an approval is an **insert-once** operation keyed by `idempotency_key`:

1. Attempt to record the approval in `gate_events` (the `idempotency_key` column is UNIQUE).
2. **First** insert for a key → the gate advances (the decision is applied to `SpiralState`).
3. **Subsequent** insert with the same key → the UNIQUE constraint rejects it; the handler treats it as
   *already processed* and performs **no state change** (idempotent no-op).

Suppression is enforced by the database constraint, so correctness does not depend on agent behavior.

### 3. Reordering tolerance — apply only to the current pending gate

Before applying, the handler checks that the approval's `gate_id` is the project's **current pending
gate** (`SpiralState.pending_gate_id`). Approvals that reference an already-resolved or non-pending gate
(stale or reordered messages) are **ignored and logged**, so a delayed/reordered message cannot move a
gate that has since changed. This is the concrete meaning of `tolerate_message_reordering: true`.

### 4. TTL — 72-hour honor window

`approval_idempotency_ttl_hours` (72h) is the window during which a pending approval request is
honored. An approval that references a gate whose pending request is older than the TTL is rejected as
**stale** (the user is asked to act on a fresh prompt). The TTL also bounds how long suppression
records must be retained for replay protection; pruning `gate_events` older than the window is a later
maintenance concern, not part of S05.02.

### 5. Boundaries

- **Key generation** and the **pending-gate check** are orchestration/policy concerns; the **Telegram
  adapter** only carries the key in/out and never interprets it.
- **Duplicate suppression** is persistence: it uses the `gate_events` table via a typed port/adapter
  (consistent with "ports before adapters"). S05.02's testable core is the *idempotent
  record-and-advance* component, keyed by `idempotency_key`, with the pending-gate guard.

## Implementation plan (S05.02, Codex lead / Claude review)

An idempotency component that, given `(project_id, gate_id, idempotency_key, decision)`:
records the approval once in `gate_events` and reports whether it **advanced** or was a **duplicate**,
gated by a pending-gate check. *Acceptance:* applying the same key twice advances state exactly once;
two distinct keys advance distinctly; an approval for a non-pending gate is ignored. Tests use a real
SQLite database (the Phase 4 schema).

## Consequences

- **Positive:** double-advance is impossible at the database layer regardless of agent behavior; the
  key lifecycle is explicit; reordering is handled by a state check, not heuristics; builds directly on
  the existing `gate_events` schema.
- **Trade-off:** the orchestrator must generate and thread the key through the Telegram round-trip
  (callback_data), which S05.02 sets up at the persistence layer and a later Telegram-wiring slice
  completes end-to-end.
- **Deferred:** TTL-based pruning/sweeping of old `gate_events`; full end-to-end Telegram callback
  wiring (this slice proves the dedup mechanism).

## Alternatives considered

1. **Deduplicate in agent/process memory.** Rejected: not durable across restarts and trusts the
   agent — a buggy agent could double-apply. Guardrail #7 requires the control to live outside agent code.
2. **Key = `project_id:gate_id` only (no nonce).** Rejected: cannot distinguish a legitimate
   re-approval after a `revise` from a replay of the prior approval — the second approval would be
   wrongly suppressed.
3. **Application-level "have I seen this?" check before insert (read-then-write).** Rejected in favor of
   relying on the UNIQUE constraint (INSERT-once), which is atomic and race-free.

## What you are approving

The key scheme (`project_id:gate_id:nonce`, generated per request), INSERT-once duplicate suppression
via the `gate_events` UNIQUE constraint, the pending-gate reordering guard, and the 72-hour honor
window — as the basis for S05.02. Approve by merging this ADR PR (or comment with changes); the loop
then implements S05.02 against it.
