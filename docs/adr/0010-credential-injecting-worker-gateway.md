# ADR-0010: Credential-injecting gateway — keyless workers for the live run

- **Status:** accepted (supersedes the ADR-0009 worker-auth relaxation)
- **Date:** 2026-06-22
- **Deciders:** founder (Pat — "what is best practice; let's not cut corners") + Claude Code (lead); Codex (review)
- **Relates to:** ADR-0004 (cost gateway), ADR-0007 (containment), ADR-0009 (egress gateway), `scoped-credentials`

## Context

ADR-0009 proposed, for the first run, putting the operator's provider API keys **inside** the
worker container — a documented relaxation of D6 ("workers don't hold the orchestrator's
long-lived keys"). The founder asked for **best practice** instead. Best practice is that the
worker holds **no credential at all**: a secret that never enters the workload cannot be leaked,
exfiltrated, or read by a rogue or prompt-injected worker.

The blocker had been: the Claude/Codex CLIs call the providers directly. **Verified empirically**
that they honor a custom base URL and run with *any* key value — a `claude` invocation with
`ANTHROPIC_BASE_URL` pointed at a local listener and a **dummy** key routed straight to the
listener carrying the dummy key. So a transparent gateway can sit in front without TLS-MITM.

## Decision

A **credential-injecting gateway** — a small reverse proxy, on the host side (the proxy
container) — holds the real provider keys. Workers are **keyless**:

- The worker container gets `ANTHROPIC_BASE_URL` / the Codex provider base URL pointed at the
  gateway, and a **placeholder** API key (never the real one).
- The gateway receives the worker's provider request, **replaces the placeholder with the real
  key** (Anthropic `x-api-key`, OpenAI `Authorization: Bearer`), forwards to the real provider,
  and streams the response back.
- The real keys live **only** in the gateway (host side), loaded from the operator's gitignored
  secret files — never in a worker container, a prompt, a log, or an artifact.

**Defense in depth (still required):** the keys the gateway holds are **dedicated** (TalisMan-only,
not the operator's primary keys) and **spend-capped** on the provider accounts, so even the one
place they live has a bounded blast radius.

**Network:** the gateway is the dual-homed container of ADR-0009 (workers' `--internal` network +
an egress network). Workers reach only the gateway by name; the gateway reaches only the
allowlisted providers. For a first run that only needs the providers, the gateway is the worker's
sole egress; the CONNECT egress proxy (S16.19) remains for any non-provider egress (git, packages).

## Consequences

- **Keyless workers**: a rogue/injected worker has no real key to steal or push anywhere. This is
  the proper foundation for *unattended* autonomous operation — the whole point of the deployment.
- This **resolves** the ADR-0009 worker-auth relaxation: the operator does not put raw provider keys
  in workers. The `scoped-credentials` follow-up (rotating/short-lived gateway keys) is a refinement,
  not a prerequisite.
- The gateway is security-critical (it handles keys + streams responses); it is built carefully and
  **validated locally end-to-end** before deployment.
- Metering worker spend through this gateway (tying into ADR-0004 budget) is a possible later
  extension; for the first run, the provider-side spend cap bounds cost.

## Alternatives considered

- **Raw keys in the worker (ADR-0009 relaxation)** — rejected by the founder; not best practice; a
  rogue worker could read the key, and an allowlisted host (e.g. GitHub) is a potential exfil path.
- **TLS-terminating MITM injection** — unnecessary: the CLIs accept a custom base URL, so the
  gateway sits in front transparently without cracking TLS (and hand-rolled MITM is itself risky).
- **Per-run dedicated keys in the worker, capped** — acceptable "good practice", but still places the
  secret in the workload; kept only as the gateway's own defense-in-depth, not in the worker.
