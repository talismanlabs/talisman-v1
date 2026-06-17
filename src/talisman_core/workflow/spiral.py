"""LangGraph spiral workflow mechanics (Phase 3).

Implements the gated project spiral defined in ADR-0002: a LangGraph ``StateGraph``
over a plain, serializable ``SpiralState`` with one node per spiral phase and routing
driven by the policy-computed ``phase_sequence``. LangGraph owns workflow mechanics
only — tiering, gate-ness, and side effects enter through injected handlers
(guardrail #2). Gate interrupt/resume is supplied by policy-injected gate phases.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from talisman_core.ports.approval import ApprovalDecision

# LangGraph's END sentinel is the string "__end__"; bind it to a str-typed name so
# the router can return it without leaking Any out of the workflow layer.
_END: str = END

SPIRAL_PHASES: tuple[str, ...] = (
    "interview",
    "discovery",
    "synthesis",
    "plan",
    "red_team",
    "slice_approval",
    "implementation",
    "review",
    "retro",
)
"""Canonical ordered spiral phases. A project's active phases are a policy-chosen
subset (the ``phase_sequence``), so tiering lives in policy, not in the graph."""


class SpiralState(TypedDict):
    """Serializable LangGraph state for one project spiral (see ADR-0002).

    Plain types only (strings, lists, ints, optionals) so checkpointing stays easy
    to debug and audit. ``phase_sequence`` is computed by policy at intake; the graph
    only walks the sequence it is given.
    """

    project_id: str
    tier: str
    phase_sequence: list[str]
    current_phase: str
    completed_phases: list[str]
    pending_gate_id: str | None
    last_decision: str | None
    artifacts: list[str]
    escalations_today: int


class GateInterruptPayload(TypedDict):
    """Serializable payload surfaced by LangGraph when a phase awaits approval."""

    project_id: str
    gate_id: str
    phase: str
    summary: str


# A phase handler performs the real work of a phase and optionally returns an
# artifact identifier to record. Handlers are injected so vendor/effectful behavior
# never enters the workflow layer. None is used when no handler is supplied for a phase.
PhaseHandler = Callable[[SpiralState], str | None]


def next_active_phase(state: SpiralState) -> str:
    """Return the next active phase to run, or END when the sequence is exhausted.

    "Active" means present in ``phase_sequence`` and not yet in ``completed_phases``.
    Phases absent from the sequence (auto-passed for the tier) are never entered, so
    tiering needs no special-casing in the graph.
    """

    if state["last_decision"] == ApprovalDecision.REJECT.value:
        return _END

    for phase in state["phase_sequence"]:
        if phase not in state["completed_phases"]:
            return phase
    return _END


def _gate_id(state: SpiralState, phase: str) -> str:
    """Return a deterministic gate id for a project's phase gate."""

    return f"{state['project_id']}:{phase}"


def _gate_payload(state: SpiralState, phase: str, gate_id: str) -> GateInterruptPayload:
    """Build the approval payload surfaced to the orchestrator."""

    return {
        "project_id": state["project_id"],
        "gate_id": gate_id,
        "phase": phase,
        "summary": f"Approval required for phase '{phase}'.",
    }


def _coerce_approval_decision(value: object) -> ApprovalDecision:
    """Normalize a resumed interrupt value to an ApprovalDecision."""

    if isinstance(value, ApprovalDecision):
        return value
    if isinstance(value, str):
        return ApprovalDecision(value)
    message = "Approval resume value must be an ApprovalDecision or decision string."
    raise TypeError(message)


def _record_phase_artifact(
    phase: str,
    state: SpiralState,
    handlers: Mapping[str, PhaseHandler] | None,
) -> list[str]:
    """Run a phase handler, when supplied, and return the updated artifact list."""

    artifacts = list(state["artifacts"])
    if handlers is not None and phase in handlers:
        produced = handlers[phase](state)
        if produced is not None:
            artifacts.append(produced)
    return artifacts


def _complete_phase(phase: str, state: SpiralState) -> list[str]:
    """Return completed phases with the current phase recorded once."""

    if phase in state["completed_phases"]:
        return list(state["completed_phases"])
    return [*state["completed_phases"], phase]


def _decision_update(
    phase: str,
    state: SpiralState,
    decision: ApprovalDecision,
) -> dict[str, Any]:
    """Convert a human approval decision into a LangGraph state update."""

    if decision is ApprovalDecision.APPROVE:
        return {
            "current_phase": phase,
            "completed_phases": _complete_phase(phase, state),
            "pending_gate_id": None,
            "last_decision": decision.value,
        }
    if decision is ApprovalDecision.REVISE:
        return {
            "current_phase": phase,
            "pending_gate_id": None,
            "last_decision": decision.value,
        }
    if decision is ApprovalDecision.PAUSE:
        return {
            "current_phase": phase,
            "pending_gate_id": state["pending_gate_id"],
            "last_decision": decision.value,
        }
    return {
        "current_phase": phase,
        "pending_gate_id": None,
        "last_decision": ApprovalDecision.REJECT.value,
    }


def _make_phase_node(
    phase: str,
    handlers: Mapping[str, PhaseHandler] | None,
    gate_phases: frozenset[str],
) -> Callable[[SpiralState], dict[str, Any]]:
    """Build the node function for one spiral phase.

    The node marks the phase current and completed and delegates any real work to an
    injected handler. If policy marks the phase as a gate, the node records a
    checkpointed pending gate before interrupting, then routes based on the resumed
    ``ApprovalDecision`` value.
    """

    def run_phase(state: SpiralState) -> dict[str, Any]:
        if phase in gate_phases:
            gate_id = _gate_id(state, phase)
            if state["pending_gate_id"] == gate_id:
                decision = _coerce_approval_decision(
                    interrupt(_gate_payload(state, phase, gate_id))
                )
                return _decision_update(phase, state, decision)

            return {
                "current_phase": phase,
                "pending_gate_id": gate_id,
                "artifacts": _record_phase_artifact(phase, state, handlers),
            }

        return {
            "current_phase": phase,
            "completed_phases": _complete_phase(phase, state),
            "pending_gate_id": None,
            "artifacts": _record_phase_artifact(phase, state, handlers),
        }

    return run_phase


def build_spiral_graph(
    handlers: Mapping[str, PhaseHandler] | None = None,
    checkpointer: Any | None = None,
    gate_phases: set[str] | None = None,
) -> Any:
    """Compile the LangGraph spiral.

    One node per spiral phase; conditional routing (at entry and after each phase)
    selects the next active phase from ``phase_sequence`` or ends. ``handlers`` and
    ``checkpointer`` are injected by the application composition root, keeping the
    workflow free of concrete infrastructure. ``gate_phases`` is the policy-injected
    set of phases that require human approval; omit it for an ungated graph. Returns
    a compiled LangGraph runnable.
    """

    gate_phase_names = frozenset(gate_phases or ())
    if gate_phase_names and checkpointer is None:
        message = "Gate phases require an injected LangGraph checkpointer."
        raise ValueError(message)

    builder = StateGraph(SpiralState)
    for phase in SPIRAL_PHASES:
        # langgraph's heavily-overloaded add_node does not accept a dynamically built
        # partial-update node under mypy --strict; run_phase returns a valid partial
        # state dict at runtime (verified by tests).
        builder.add_node(  # type: ignore[call-overload]
            phase,
            _make_phase_node(phase, handlers, gate_phase_names),
        )

    route_map: dict[Hashable, str] = {phase: phase for phase in SPIRAL_PHASES}
    route_map[_END] = _END

    builder.add_conditional_edges(START, next_active_phase, route_map)
    for phase in SPIRAL_PHASES:
        builder.add_conditional_edges(phase, next_active_phase, route_map)

    return builder.compile(checkpointer=checkpointer)
