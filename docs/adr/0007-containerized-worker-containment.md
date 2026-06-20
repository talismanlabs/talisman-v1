# ADR-0007: Containerized, proxy-only-networked worker containment

- **Status:** accepted
- **Date:** 2026-06-20
- **Deciders:** Pat (founder) — "index on full autonomy" (2026-06-20). Implemented from S16.06.
- **Context slice:** v1.1-P1 consolidation; **part 2 of** audit finding **P0-B** (egress as a real
  boundary, not a cooperative one). The containment that lets AT-14 become a true PASS.

## Context

S16.04 built the egress proxy — the allowlist *decision point* — but Codex correctly flagged it as a
**cooperative** control: a worker can open a direct socket or unset `HTTPS_PROXY` and bypass it. A real
boundary requires something that makes the proxy the worker's *only* route to the network.

Pat then chose to **index on full autonomy**: TalisMan should run unattended on an always-on host while
keeping the blast radius to a sacrificial box. Both goals point at the same mechanism.

## Decision

Run each worker inside a **rootless podman container** attached to an **`--internal` network** whose
only reachable peer is the egress proxy. Because an `--internal` network has no route off-host, the
worker **physically cannot reach the internet except through the proxy** — it cannot bypass what it has
no route to.

**Empirically verified (2026-06-20, podman 4.9.3 rootless):** a container on a normal network reaches
`1.1.1.1` / `api.anthropic.com`; the *same* container on an `--internal` network gets `Network
unreachable` to both. The boundary is enforced by the kernel/network, not by worker cooperation.

**Topology (deployment):**

```
            ┌─────────── internal net (no off-host route) ───────────┐
   worker container ──▶ egress proxy ──┐                              │
   (no other route out)                │                             │
            └────────────────────────  │  ─────────────────────────  ┘
                                        ▼
                              external net ──▶ internet (allow-listed hosts only)
```

The egress proxy (S16.04) is the single chokepoint and the only container bridging the internal and
external networks; it enforces the `security.egress` allowlist on everything that leaves.

Additional properties this buys:
- **Credential isolation, reinforced:** a container starts with a *clean* environment (no host env is
  inherited), so the orchestrator's provider keys are never present in a worker. Model calls route
  through the gateway/proxy rather than carrying raw keys (complements S16.03 / AT-13).
- **Filesystem isolation:** only the explicit workspace mount is visible to the worker.

**Why podman (rootless):** it is already present here, runs without a daemon or root, and supports
`--internal` networks — so the strongest containment needs no privileged host changes. Docker is a
drop-in for the same invocation.

## Consequences

- **This slice (S16.06):** delivers the **container-isolation runner** (`workers/_container.py`, a
  drop-in `CommandRunner` that wraps a worker command in an isolated `podman run`) plus a **proof** —
  an integration test showing an `--internal`-network container cannot egress. This is the boundary
  *mechanism*, proven.
- **AT-14 stays COMPONENT_VERIFIED** here, deliberately. The mechanism is built and proven, but the
  running orchestrator does not yet execute workers through it end-to-end. AT-14 flips to PASS in the
  **wiring follow-up**, when the composition root runs real workers via the container runner with the
  proxy as a sibling, proven by an allow/deny-and-no-bypass integration test. **No grade is inflated
  in S16.06** (avoiding the S16.04 over-claim).
- **Required follow-ups:** (1) a worker image carrying the `claude` / `codex` CLIs; (2) wire the
  container runner + a running proxy into the composition; (3) route worker model calls through the
  gateway; (4) deploy to the always-on dedicated box (operational, needs the founder's cloud account).
- **Test posture:** the container integration test self-skips where podman or `--internal` networks are
  unavailable, so the deterministic gate never depends on a container runtime; command construction is
  covered by fast unit tests that always run.
