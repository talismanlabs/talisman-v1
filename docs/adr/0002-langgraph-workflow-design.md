# ADR-0002: Phase 3 LangGraph spiral workflow design

- **Status:** Proposed (pending human approval — this ADR resolves a known spec gap before Phase 3
  implementation begins)
- **Date:** 2026-06-17
- **Deciders:** Pat (human, approver), Claude Code (author)
- **Related:** `docs/talisman-v1/talisman-v1-architecture-final.md` (D1, D2), the canonical
  `workflow/spiral.py` scaffold in `talisman-v1-config-templates.md`, guardrail #2 ("LangGraph owns
  workflow mechanics only"), slice backlog S03.01 / S03.02, acceptance test AT-04.

## Context

Phase 3 ("LangGraph workflow skeleton") is one of the **known specification gaps** flagged during
evaluation: the canonical scaffold defines a plain `SpiralState` TypedDict but leaves
`build_spiral_graph()` as `raise NotImplementedError`. The artifacts specify *what* the spiral is
(the gate sequences per tier) and the *boundary rule* (LangGraph owns mechanics; TalisMan owns
policy/security/review/cost) — but not the **graph shape**, the **gate → interrupt/resume model**, the
**checkpointing strategy**, or **where the LangGraph/policy line falls**. Per the build model, the
slice-runner halts on a spec gap and proposes an ADR rather than guessing. This is that ADR.

Approving it unblocks S03.01 (spiral state + graph compile) and S03.02 (approval interrupt + resume),
and gives those slices concrete, reviewable acceptance targets.

What is already fixed by the artifacts (not re-decided here):

- **Tiers & gate sequences** (`config.yaml` → `workflow.tiers`):
  - `full_spiral`: `interview → discovery → synthesis → plan → red_team → slice_approval →
    implementation → review → retro`
  - `lightweight`: `interview → plan → slice_approval → review → retro` (auto-passes `discovery`,
    `red_team`).
- **Boundary rule** (guardrail #2): policy, security, review routing, cost, and Telegram formatting
  live *outside* LangGraph.

## Decision (proposed)

### 1. `SpiralState` — plain, serializable, checkpoint-friendly

Keep the artifact's plain TypedDict (strings/lists/ints/bools only — easy to checkpoint and audit),
extended minimally so the graph can route without embedding policy:

```python
class SpiralState(TypedDict):
    project_id: str
    tier: str                      # "lightweight" | "full_spiral"
    phase_sequence: list[str]      # ordered active phases for this project (computed by POLICY at intake)
    current_phase: str
    completed_phases: list[str]
    pending_gate_id: str | None    # set while paused at a gate awaiting a human decision
    last_decision: str | None      # the ApprovalDecision value that last resumed a gate
    artifacts: list[str]           # artifact ids/paths produced so far
    escalations_today: int
```

Crucially, `phase_sequence` is **computed by the policy layer at intake** (from tier + auto-pass
rules) and handed to the graph. The graph never decides *which* phases exist — it only walks the
sequence it is given. This keeps tiering in policy, mechanics in LangGraph.

### 2. Graph topology — explicit per-phase nodes, sequence-driven routing

Build one `StateGraph(SpiralState)` with **one node per spiral phase** (`interview`, `discovery`,
`synthesis`, `plan`, `red_team`, `slice_approval`, `implementation`, `review`, `retro`). Explicit
nodes keep the spiral visible and auditable ("aggressively boring") rather than hiding it in a generic
loop. Routing is driven by `phase_sequence`:

- `START → <first phase in phase_sequence>`.
- After each phase node, a single conditional edge (`advance`) consults `phase_sequence` /
  `completed_phases` to pick the next active phase, or routes to `END` when the sequence is exhausted.
- Phases absent from `phase_sequence` (e.g. `discovery`/`red_team` under `lightweight`) are simply
  never entered — the auto-pass behaviour falls out of the sequence, no special-casing in the graph.

Each phase node does **no business work itself**. It updates `SpiralState` (mark phase entered/done,
append artifact ids) and delegates any real effect to injected handlers (see §5). This is the
mechanics/policy seam.

### 3. Gates → human-in-the-loop interrupts

A phase is a **gate** when it requires a human decision. Which phases are gates is supplied by
**policy** (not hardcoded in the graph), consistent with the tier's gate list. At a gate, the node
calls LangGraph's `interrupt(payload)` (from `langgraph.types`) with a payload describing the gate
(`project_id`, `gate_id`, the phase, a human-readable summary). This **pauses** the graph and persists
state via the checkpointer.

- The orchestrator (app layer) surfaces that payload to the human through the **`ApprovalPort`**
  (Telegram in production; a fake in tests) — the graph itself imports no adapter.
- The human's `ApprovalDecision` resumes the graph via `graph.invoke(Command(resume=decision), config)`.

Decision → routing (workflow mechanics, fine inside the graph):

| ApprovalDecision | Effect |
|---|---|
| `approve` | mark phase complete; advance to next phase in sequence |
| `revise` | re-enter the current phase (loop) with reviewer/notes context |
| `pause` | remain interrupted (no state advance) |
| `reject` | route to `END` / aborted terminal state |

**Irreversibility** (guardrail #7) is handled in policy: policy marks a phase/action as gated when it
is irreversible, so an irreversible action simply *is* a gate. The graph needs no special irreversible
logic — it honours "this phase is a gate."

### 4. Checkpointing & resume (AT-04)

The graph is compiled with an **injected** `BaseCheckpointSaver`; the workflow never hardcodes a store
(keeps `workflow` free of infrastructure):

- **Tests / Phase 3:** `MemorySaver` (in-process pause/resume).
- **Durable / AT-04 cross-restart resume:** a SQLite-backed saver (`SqliteSaver`) injected by the app
  layer in **Phase 4**, keyed by `thread_id = project_id`. "Restart the process, approve the gate,
  project resumes from checkpoint" then works because state lives in the checkpoint store, not memory.

So S03.02 demonstrates pause/resume with `MemorySaver`; AT-04's restart-durability is satisfied once
Phase 4 injects the SQLite saver. The interface is identical; only the injected saver changes.

### 5. The LangGraph / policy seam (resolves the flagged ambiguity)

| Concern | Owner | How it enters the graph |
|---|---|---|
| State schema, nodes, edges, interrupt/resume, checkpointing, spiral topology | **LangGraph (workflow)** | native |
| Which phases run (tiering) | **policy** | precomputed `phase_sequence` in state |
| Which phases are gates; irreversibility → gate | **policy** | injected `is_gate(phase, state)` predicate |
| Approval decision | **`ApprovalPort`** | injected; orchestrator calls it on interrupt |
| Running a worker, discovery, etc. | **`WorkerPort` / policy** | injected phase handlers |
| Cost pre-checks, escalation, review routing | **policy / `GatewayPort`** | injected; invoked by the orchestrator around phases |

`workflow` may import `talisman_core.domain` and `talisman_core.ports` only — never adapters/workers
(now enforced for ports by S02.03; `workflow → adapters/workers` is already forbidden by the
`workflow_uses_ports_not_adapters` contract). `langgraph` is added to `pyproject` runtime deps in
S03.01 (the first slice that needs it).

## Implementation plan (governed slices)

- **S03.01 — spiral state + graph compile** (Claude lead / Codex review). Finalize `SpiralState`; add
  `langgraph` runtime dep; implement `build_spiral_graph(handlers, checkpointer)` that compiles a
  `StateGraph` with the phase nodes and sequence-driven routing. *Acceptance:* serializable state +
  graph compiles; a unit test compiles the graph and walks a trivial `phase_sequence` to `END`.
- **S03.02 — approval interrupt + resume** (Codex lead / Claude review). Add `interrupt()` at gate
  phases and resume via `Command(resume=decision)`, using `MemorySaver` and a fake `ApprovalPort`.
  *Acceptance:* a fake gate pauses with `pending_gate_id` set and resumes after a decision; the four
  decision routes behave per the table above.

## Consequences

- **Positive:** the spiral is explicit and auditable; tiering/gates/cost/irreversibility stay in
  policy (guardrail #2 upheld); checkpointer injection keeps `workflow` infrastructure-free and makes
  AT-04 a Phase-4 wiring detail, not a redesign; S03.01/02 get concrete acceptance targets.
- **Trade-off:** one node per phase is more boilerplate than a generic loop, accepted for auditability.
- **Deferred:** escalation-score computation (D1 `T=0.70`) and review routing are policy concerns for
  later phases; this ADR only requires that gates can pause/resume, not how escalation is scored.

## Alternatives considered

1. **Generic `work`/`gate` node loop parameterized by `current_phase`.** Rejected for v1: more
   compact but hides the spiral; explicit nodes are easier to review and reason about.
2. **`interrupt_before=[gate_nodes]` at compile time** instead of the `interrupt()` function. Viable,
   but static `interrupt_before` can't express "this phase is a gate *for this tier/state*"; the
   `interrupt()` + `Command(resume=)` pattern lets policy decide gate-ness at runtime. Recorded as a
   fallback if the dynamic API proves awkward.
3. **Embed tiering/gate logic inside graph nodes.** Rejected: violates guardrail #2 (policy would
   leak into LangGraph).

## What you are approving

That S03.01/S03.02 implement: the `SpiralState` above; explicit per-phase nodes with
`phase_sequence`-driven routing; gates via `interrupt()` + `Command(resume=ApprovalDecision)` with the
four decision routes; an injected checkpointer (`MemorySaver` now, `SqliteSaver` in Phase 4); and the
LangGraph/policy seam in §5. Approve by merging this ADR PR (or comment with changes). On approval the
loop resumes at S03.01.
