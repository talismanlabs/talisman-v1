# ADR-0005: Phase 14 bootstrap self-improvement project — assemble + simulated run

- **Status:** Accepted (the user chose "Assemble + simulated run" in a design review on 2026-06-18)
- **Date:** 2026-06-18
- **Deciders:** Pat (human, approver), Claude Code (author)
- **Related:** master-build-roadmap Phase 14; architecture decisions D1 (gated spiral), D3 (cross-family
  review), D8 (scheduler); ADR-0002 (LangGraph workflow), [[talisman-v1-acceptance-test-plan]]

## Context

Phases 0–13 each delivered a **well-tested core** — domain, ports, the LangGraph workflow, SQLite
state, approval policy, both worker adapters, the review-enforcement policy, the cost gateway, the
security profile, the scheduler, observability, and the systemd units — every one green and
cross-reviewed. But those are **verified parts, not yet an assembled running service**: there is no
composition root wiring the layers together, no `talisman_core.main` entrypoint (the systemd unit
already references one), and a few "live" pieces were intentionally scoped out of the testable slices —
notably lessons/memory retrieval and a live Telegram bot.

Phase 14's roadmap goal is *"TalisMan runs its first project — planning its own v1.1 — through the
gates."* That presumes an assembled, runnable TalisMan, so Phase 14 is the **integration capstone**, not
another single module. The phase was flagged under-specified; the open question was *how far to take it*.

## Decision

**Assemble the system and run one governed self-improvement planning spiral deterministically.** We build
the composition root and entrypoint, wire the existing layers, and execute a single end-to-end gated
spiral over the "plan TalisMan v1.1" project in a **deterministic / simulated** mode — **no live API
spend, fully testable in CI**. The run produces TalisMan's real v1.1 improvement backlog as its artifact
and proves the assembled loop executes and the gates actually fire.

The simulated run uses, in place of live infrastructure (all of which are wired through their existing
ports, so swapping to live is a later step, not a rewrite):

- **Workers:** a deterministic stub worker behind the existing `WorkerPort` (no live Claude/Codex, no spend).
- **Approval:** an in-process approver behind the approval port (the gate pauses and resumes) instead of a
  live Telegram bot — the allowlist/idempotency logic from Phase 5 is already built.
- **Gateway:** the gateway client over a stub transport (no live provider call).
- **Lessons:** a minimal retrieval path over the existing `lessons` table, added only if the run needs it.

A **full live run** (real workers, running gateway, live Telegram, host install, real spend) remains the
truest proof but is an **operations milestone for after v1 acceptance**, not part of the build.

## Implementation plan (Phase 14 slices)

- **S14.01 — composition root + entrypoint** (Claude lead / Codex review). `app/composition` wires the
  layers with injected adapters; `talisman_core/main` is the entrypoint the systemd unit references, with
  a build-and-validate (dry-run) path. Acceptance: the app assembles and runs a trivial cycle
  deterministically.
- **S14.02 — governed self-improvement spiral run** (lead TBD / opposite-family review). Define the
  "plan TalisMan v1.1" project, run one full gated spiral (propose → cross-family review gate → approval
  gate → record) deterministically, and emit the v1.1 improvement backlog artifact. Acceptance: the gates
  fire and the artifact is produced — *"TalisMan completes one governed self-improvement planning spiral."*
- **S14.03 — minimal lessons retrieval** (only if S14.02 needs it) — a thin read path over the existing
  `lessons` table.

## Consequences

- **Positive:** proves the system is a coherent, runnable whole (the honest gap), fills the assembly we
  need regardless, produces TalisMan's actual v1.1 roadmap, and stays in the safe/cheap/testable lane the
  whole build has used. The capstone is reviewable in CI like every other slice.
- **Trade-off:** the deterministic run does not exercise live workers, the live gateway, or live Telegram;
  those are first exercised at operator install and the Phase 15 acceptance run (AT-18 etc.).
- **Deferred:** the full live self-improvement run (Option B) — a post-acceptance operations milestone;
  the live Telegram bot runtime; richer lessons embedding/retrieval.

## Alternatives considered

- **Full live deployment + real run (Option B).** Truest proof, but an operations/deployment effort
  outside CI (host install, bot token, real spend) needing the deferred live pieces. Better once v1 is
  accepted and Pat is ready to deploy and spend.
- **Governed plan as a document (Option C).** Produce the v1.1 backlog as an artifact run through
  propose→review→approve gates only. Lightest and yields the roadmap, but does not prove the software runs
  end-to-end — too weak to call "TalisMan ran a project."

## What you are approving

That Phase 14 = assemble the orchestrator into a runnable service **and** run one deterministic
end-to-end governed v1.1-planning spiral (stub workers, in-process approval, stub gateway), decomposed
into S14.01 (composition + entrypoint) and S14.02 (the governed run), with a full live run deferred to
post-v1 operation.
