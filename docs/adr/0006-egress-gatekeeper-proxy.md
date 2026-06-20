# ADR-0006: Egress enforcement via a local gatekeeper (CONNECT) proxy

- **Status:** accepted
- **Date:** 2026-06-20
- **Deciders:** Pat (founder) chose the gatekeeper-proxy approach on 2026-06-20; implemented in S16.04.
- **Context slice:** v1.1-P1 consolidation; delivers **part 1 (the decision point) of** 2026-06-19 audit
  finding **P0-B** (the egress allowlist was a pure policy that no networked code called — advisory, not
  enforced). Full closure also needs part 2 (OS-level containment, below). Relates to AT-14.

## Context

`security/egress.py` defines a correct default-deny allowlist (`is_allowed` / `ensure_allowed`), but
nothing consults it at runtime: the orchestrator's `httpx` clients and — more importantly — the worker
subprocesses (Claude Code, Codex CLI) can reach any host. For a system that runs semi-autonomous
agents with network access, the real risk is a prompt-injected or compromised worker exfiltrating data
or fetching attacker payloads. An allowlist that nothing enforces does not mitigate that.

Two enforcement shapes were considered:

- **Per-client in-app check** — call `ensure_allowed` inside each `httpx` client. Small, but only
  covers the orchestrator's *own* calls; a worker subprocess bypasses it entirely. Rejected as the sole
  mechanism — it leaves the main exfiltration path open.
- **Gatekeeper proxy (chosen)** — a single local checkpoint that *all* traffic (orchestrator **and**
  worker subprocesses) is routed through; it permits a connection only to an allowlisted host.

## Decision

Build a **local forward proxy** (`adapters/egress_proxy.py`) as the egress allowlist's **decision
point**. The orchestrator and worker subprocesses are to reach the network only through it — but that
binding is created by OS-level containment (see "Enforcement is two parts"), not by `HTTPS_PROXY` alone,
which is cooperative. The proxy:

- It handles the HTTPS **`CONNECT`** method: it parses the target host, calls the egress policy
  (`security.egress.is_allowed`), and either opens a blind TLS tunnel (allowed) or returns **403**
  (denied). Because it only sees the CONNECT target host — never the TLS-encrypted payload — it
  controls *where* traffic may go without inspecting *what* is sent.
- It binds to loopback (`127.0.0.1`) and fails closed: any non-`CONNECT` request is refused (`501`),
  and any host not on the allowlist is refused (`403`).
- The allow predicate is injectable so the enforcement mechanism is unit/integration-testable
  independently of the specific allowlist.

A custom in-repo Python proxy is preferred over an external `squid` dependency: it is typed, testable
under `pytest`, has no system-package footprint, and reuses the existing `security.egress` policy as the
single source of truth (resolving the S10.02 "host- vs domain-granularity" note — there is now one
policy).

## Enforcement is two parts (do not conflate them)

A proxy by itself is a **cooperative** control: it constrains only clients that choose to route through
it. A worker subprocess — especially a prompt-injected or compromised one — can open a direct socket,
unset `HTTPS_PROXY`, or use a tool that ignores it, and egress freely. So egress enforcement is two
parts, and this slice delivers only the first:

1. **Decision point (this slice, S16.04):** the proxy that evaluates each destination against
   `security.egress` and allows/denies it. Built and integration-tested.
2. **Containment (required follow-up — NOT in this slice):** an OS-level control that makes the proxy
   the *only* route to the network — e.g. running workers in a network namespace with no default route,
   `nftables`/`iptables` rules that DROP all egress except to the proxy address, or an equivalent
   sandbox. Without part 2 the allowlist remains advisory for anything that declines the proxy.

## Consequences

- **Now (S16.04):** part 1 (the decision point) exists and is proven by integration tests. This is a
  prerequisite for, **not** a completion of, audit finding **P0-B**.
- **AT-14 stays COMPONENT_VERIFIED** and flips to PASS only when part 2 is in place and a test proves
  that direct (non-proxy) egress from a worker is blocked. Env-var routing (`HTTPS_PROXY`) alone does
  **not** earn the flip. No grade is inflated in S16.04.
- **Required follow-up slice:** implement part 2 (containment), then wire the proxy URL into the worker
  environment (building on the S16.03 scrub) and the orchestrator's `httpx` clients, with the proxy
  running as a service ordered before the workers.
- **Scope limit:** plain-HTTP proxying (absolute-form requests) is intentionally refused for now; the
  allowlisted HTTP-only hosts (apt/deb mirrors) are not worker-runtime paths. Adding authenticated HTTP
  forwarding is a future extension if needed.
