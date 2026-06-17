# ADR-0004: Cost gateway — direct provider forwarding, port-first

- **Status:** Accepted (the user chose "Direct, port-first" in a design review on 2026-06-17)
- **Date:** 2026-06-17
- **Deciders:** Pat (human, approver), Claude Code (author)
- **Related:** architecture decision D5 (layered budget caps, gateway-level enforcement), D6 (keys out
  of workers), `ports/gateway.py` (the `GatewayPort` from S02.02), the `talisman_gateway.py` host-side
  scaffold and `brain/adapter.py` client scaffold in `talisman-v1-config-templates.md`, slices
  S09.01 / S09.02.

## Context

Phase 9 (cost gateway) is a known specification gap. The artifacts require that **all** orchestrator
model calls route through a budget/credential gateway ("LiteLLM or equivalent") and that the
orchestrator never calls Anthropic/OpenAI directly — but they do not decide **how the gateway forwards
a call to a provider**. This was surfaced to the human as a plain-English design choice (convenience +
many providers via LiteLLM, vs. control + minimal dependencies via direct adapters). The human chose
**direct, port-first**.

The gateway exists to deliver three product guarantees: (1) **spending safety** — budget caps enforced
*before* a call, outside agent code so a buggy/looping agent cannot bypass them; (2) **key safety** —
provider keys live in the gateway, never inside worker agents (D6); (3) **provider flexibility** —
providers can be swapped or mixed without rewriting the core.

## Decision

1. **Topology.** The gateway is a **host-side service** that holds provider keys, enforces budget
   pre-call, and forwards model requests to providers. The orchestrator reaches it only through the
   typed `GatewayPort`; it never imports a provider SDK or calls a provider directly.
2. **Forwarding = direct, not LiteLLM.** Provider forwarding uses **thin, hand-written per-provider
   adapters** (Anthropic, OpenAI). Rationale: v1 uses exactly two providers; this keeps runtime
   dependencies minimal and control high ("aggressively boring"). LiteLLM's main benefit (100+
   providers, swap-by-config) is not needed for a two-provider v1.
3. **LiteLLM stays a future option behind the port.** Because forwarding sits behind `GatewayPort`,
   adopting LiteLLM later (if many providers or its cost-tracking become worthwhile) requires **no core
   changes** — only a new adapter. This preserves the artifacts' "swap-friendly gateway" intent.
4. **Budget enforcement lives in the gateway, recorded durably.** Pre-call accounting and the
   daily/monthly hard caps are enforced server-side and written to the state database (the `budget_events`
   table), so enforcement does not depend on agent behavior.

## Implementation plan (Phase 9 slices)

- **S09.01 — gateway adapter** (Claude lead / Codex review). A client adapter implementing `GatewayPort`
  that routes a `GatewayRequest` to the gateway and returns a `GatewayResult`, via an **injected
  transport** so it is testable without a live gateway or any provider call. *Acceptance:* model calls
  route through the gateway port (no direct provider import in the core).
- **S09.02 — budget circuit breakers** (Codex lead / Claude review). Pre-call accounting + simulated
  daily/monthly cap that pauses work, recorded to `budget_events`. *Acceptance:* a simulated cap breach
  pauses execution before a provider request.

The **real provider HTTP forwarding** (the direct Anthropic/OpenAI calls inside the gateway service) is
wired when the orchestrator's "brain" first needs a model call; until then the gateway runs in a
budget-enforcing, scaffolded-forward mode. (The workers — Claude Code and Codex CLI — authenticate to
their own providers; the gateway governs the orchestrator's own model calls.)

## Consequences

- **Positive:** the budget + key-isolation safety value and the gateway boundary land now with minimal
  dependencies and full control; the design stays swappable (LiteLLM later behind the port); matches the
  "boring, modular" guardrails.
- **Trade-off:** a small hand-written adapter per provider must be maintained — acceptable at two
  providers; revisit if the provider count grows.
- **Deferred:** real direct provider HTTP forwarding (wired when the brain needs it); LiteLLM adoption
  (future, behind the port).

## Alternatives considered

1. **Adopt LiteLLM now.** Rejected: places a third-party layer in the critical path (its bugs/breakage
   become ours), adds an operational moving part, and concentrates vendor lock-in — disproportionate for
   a two-provider v1. Still available later behind the port.
2. **Defer everything (budget + boundary only, no forwarding decision).** Rejected: we want the gateway
   boundary settled now so S09.01/S09.02 have a concrete target; "direct" is a low-cost commitment that
   does not foreclose LiteLLM.

## What you are approving

The gateway as a host-side, key-holding, budget-enforcing service reached only through `GatewayPort`,
with **direct** per-provider forwarding (LiteLLM deferred behind the port), implemented by S09.01
(client adapter) and S09.02 (budget breakers). Approve by merging this ADR PR (or comment with changes).
