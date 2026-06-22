# ADR-0009: Egress gateway deployment + worker authentication for the live run

- **Status:** accepted (topology); worker-auth decision **pending founder confirmation at Stage 3**
- **Date:** 2026-06-22
- **Deciders:** founder (Pat) + Claude Code (lead); Codex (cross-family review)
- **Relates to:** ADR-0006 (egress gatekeeper proxy), ADR-0007 (containerized containment), S16.04/S16.06/S16.18

## Context

For a live run, a worker container must reach **only** the allowlisted AI providers
(`api.anthropic.com`, `api.openai.com`) — plus github + package mirrors for its work — and
nothing else, while being unable to bypass that control. The worker runs on an `--internal`
podman network (ADR-0007) with **no route off-host at all**. Two questions had no answer:

1. **How is the egress proxy reachable** from a worker on a network that, by design, can't route
   anywhere?
2. **How does the worker authenticate** to the providers (the CLIs need API credentials)?

Both were validated/decided locally with podman (same engine as the deploy box) before touching it.

## Decision — topology (accepted; proven locally)

A **dual-homed egress-gateway proxy container**:

- Two networks: `talisman-internal` (`--internal`, the workers' sealed network) and
  `talisman-egress` (a normal network with internet).
- The **proxy container** is on **both**; it runs the existing `adapters.egress_proxy.EgressProxy`
  (now with a `serve_forever` entrypoint, bound to `0.0.0.0:8888` inside the container) enforcing
  the `security.egress` allowlist.
- **Worker containers** are on `talisman-internal` **only**, with `HTTPS_PROXY=http://<proxy>:8888`
  (the proxy reached by container name). The worker's only route out is the proxy; the proxy only
  forwards to allowlisted hosts.

A **host-run** proxy was rejected: a PoC confirmed an `--internal` network blocks container→host
too, so the proxy must itself be a container on the sealed network. Per-client egress checks were
already rejected as cooperative (ADR-0006).

**Validated end-to-end locally** (real `EgressProxy`, real worker image):
- worker → `api.anthropic.com` *through the proxy* → reached (HTTP 401 over the tunnel);
- worker → `example.com` *through the proxy* → denied (not allowlisted);
- worker → `api.anthropic.com` *direct* → blocked (no route).

## Decision — worker authentication (proposed; founder confirms at Stage 3)

For the **first supervised run**, the worker container receives the operator's provider API keys
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) via its environment so the Claude/Codex CLIs authenticate.
The containment mitigates the exposure: a leaked key can't be exfiltrated anywhere except back to
the same allowlisted providers (no other egress).

This is a **deliberate, documented relaxation** of D6 ("workers don't hold the orchestrator's
long-lived keys") for the first run. The hardening — host-side scoped / short-lived per-worker
credential issuance — is the tracked `scoped-credentials` follow-up.

**This relaxation is NOT yet confirmed.** No code in this slice injects provider keys into a
worker — S16.19 builds only the network + proxy. No deploy step places provider keys, and no run
spends, until the founder explicitly confirms this D6 relaxation (a recorded approval in this ADR
+ the ledger). Until then it stays proposed/undecided.

## Consequences

- The egress gateway is the **real AT-14 boundary** in the live deployment. AT-14 flips to PASS
  once the orchestrator runs workers through it end-to-end **and** the supervised run happens.
- The proxy binds `0.0.0.0` *inside* the contained proxy container — the containment is the network
  topology, not the bind address. (Tightening to the internal-only interface is a possible later refinement.)
- The deploy script (later slice) creates the two networks, starts the proxy container, and runs
  workers with the proxy wired in.

## Alternatives considered

- **Host-run proxy reachable via the network gateway** — rejected; PoC showed `--internal` blocks
  container→host, and it's fragile.
- **Worker calls the host gateway instead of the providers directly** — rejected; the CLIs call the
  providers, and the gateway (ADR-0004) governs the *orchestrator's* spend, not the worker CLIs.
- **No worker credentials (gateway-mediated worker calls)** — out of scope for v1; the CLIs are not
  gateway-aware. Tracked as scoped-credentials hardening.
