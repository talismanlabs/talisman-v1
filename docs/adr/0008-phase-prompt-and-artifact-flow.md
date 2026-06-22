# ADR-0008: Phase prompt construction and artifact flow for live spiral runs

- **Status:** accepted
- **Date:** 2026-06-21
- **Deciders:** founder (Pat) + Claude Code (lead); Codex (cross-family review)
- **Relates to:** ADR-0002 (LangGraph workflow), ADR-0007 (containerized workers), S16.14 (live-worker wiring)

## Context

To run a real project on the `full_spiral` tier, the orchestrator must drive a real worker
(Claude Code / Codex) through nine phases:
`interview → discovery → synthesis → plan → red_team → slice_approval → implementation → review → retro`.

Today only the **canvas** is specified and built:

- The phase sequence and per-tier gates are concrete (`config-templates.md:42–47`;
  `workflow/spiral.py` `SPIRAL_PHASES`).
- `WorkerRequest` carries a `prompt_path`; the worker adapters read that file and run the CLI
  inside the no-egress container (S16.05, S16.14).
- `SpiralState.artifacts` records the list of artifacts produced so far.

But the **payload** is specified nowhere in the spec or the code:

- **No per-phase prompt.** Nothing defines what instruction a worker receives for `discovery`
  vs `synthesis` vs `red_team`, who writes the prompt file, or how it is keyed to the phase. The
  only existing handlers are deterministic stubs returning canned strings.
- **No artifact-flow policy.** Artifacts are appended to a list, but nothing defines how one
  phase's output becomes the next phase's context. No handler reads prior artifacts.
- A real run also needs two inputs the current `ProjectSpec` lacks: the project **goal** (what to
  build) and a **workspace** (the repo/dir the worker operates on, mounted into the container).

This is an under-specified slice, so per the constitution it gets a proposed ADR and a halt — no
guessing.

## Decision (proposed)

1. **Prompt construction is a pure policy.** Add `policies/phase_prompts.py` with
   `build_phase_prompt(phase, goal, prior_artifacts) -> str`; the per-phase templates live there.
   This honors guardrail 2 (workflow → policies, never infrastructure). The worker-driven handler
   (app layer) calls the policy, writes the prompt file, runs the containerized worker, and
   records the worker's output as the phase artifact.

2. **Artifacts flow as bounded context.** Each phase's worker output is written to a file in the
   workspace and its path appended to `state["artifacts"]`. The next phase's prompt includes the
   prior phases' outputs as context, bounded by a configurable character budget so a long run does
   not blow up token cost. The artifact is the durable hand-off between phases.

3. **A real project is a goal + a workspace.** `ProjectSpec` gains `goal: str`; the live run takes
   a `workspace: Path` (the project's files), mounted read-write into the worker container.

4. **Draft per-phase templates** (role + task; each also receives the bounded prior-artifact context):
   - `interview` — clarify the goal and constraints; produce a problem statement + open questions.
   - `discovery` — enumerate the relevant components, prior art, and options; produce a discovery summary.
   - `synthesis` — group the discovery findings into themes and trade-offs.
   - `plan` — produce an actionable plan / slice backlog grounded in the synthesis.
   - `red_team` — adversarially review the plan: risks, failure modes, security/safety gaps.
   - `slice_approval` — summarize the next proposed slice for human approval (gate).
   - `implementation` — implement the approved slice in the workspace as a **branch + commit, never a push to main**.
   - `review` — review the implementation for correctness, security, and adherence to the plan.
   - `retro` — write a retrospective and extract durable lessons (feeds the S16.13 lessons store).

5. **Gates stay human-approved.** In full_spiral every phase is a gate: the worker produces the
   phase's artifact, then TalisMan pauses for approval (via Telegram) before the next phase.
   `slice_approval` and `implementation` gate before any irreversible action.

## Founder decisions (2026-06-21)

- **A. Prompt content — APPROVED** as drafted above.
- **B. Context budget — APPROVED:** bounded summaries (~a few KB), not full transcripts.
- **C. Implementation output — APPROVED:** `implementation` produces a **branch + commit, gated via
  Telegram, never an auto-merge and never a push to `main`**. This is the irreversible-action boundary.
- **D. First real project — "a simple Google News replica":** the first supervised live run builds a
  small news-aggregator app, chosen as a low-risk, self-contained target to validate the live chain
  before widening the leash.

## Consequences

- Real projects become runnable: the orchestrator drives real workers through the governed spiral,
  each phase gated and each hand-off durable.
- The prompt/artifact policy is testable deterministically (pure functions); only the live run spends.
- AT-14 flips to PASS once the orchestrator runs workers through the container end-to-end (this
  wiring) and the supervised run happens.

## Alternatives considered

- **MVP single gated worker** (one worker does the whole goal, one gate). Set aside by founder
  decision (full spiral chosen); retained as a fallback if the spiral proves too costly per run.
- **Prompts in static config/YAML.** Rejected: prompt construction is behavior (depends on phase +
  artifacts), which belongs in the policy layer, not static config.
- **No artifact flow** (each phase independent). Rejected: phases must build on each other to be a
  coherent project run.
