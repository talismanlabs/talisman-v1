"""LangGraph spiral workflow mechanics (Phase 3, slice S03.01).

Implements the gated project spiral defined in ADR-0002: a LangGraph ``StateGraph``
over a plain, serializable ``SpiralState`` with one node per spiral phase and routing
driven by the policy-computed ``phase_sequence``. LangGraph owns workflow mechanics
only — tiering, gate-ness, and side effects enter through injected handlers
(guardrail #2). This slice (S03.01) covers the state schema and graph compilation;
gate interrupt/resume is added in S03.02.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

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


# A phase handler performs the real work of a phase and optionally returns an
# artifact identifier to record. Handlers are injected so vendor/effectful behavior
# never enters the workflow layer. None is used in tests and in S03.01.
PhaseHandler = Callable[[SpiralState], str | None]


def next_active_phase(state: SpiralState) -> str:
    """Return the next active phase to run, or END when the sequence is exhausted.

    "Active" means present in ``phase_sequence`` and not yet in ``completed_phases``.
    Phases absent from the sequence (auto-passed for the tier) are never entered, so
    tiering needs no special-casing in the graph.
    """

    for phase in state["phase_sequence"]:
        if phase not in state["completed_phases"]:
            return phase
    return _END


def _make_phase_node(
    phase: str, handlers: Mapping[str, PhaseHandler] | None
) -> Callable[[SpiralState], dict[str, Any]]:
    """Build the node function for one spiral phase.

    The node marks the phase current and completed and delegates any real work to an
    injected handler. In S03.01 no handlers are supplied, so the node only advances
    state — enough to compile the graph and walk a sequence to completion.
    """

    def run_phase(state: SpiralState) -> dict[str, Any]:
        artifacts = list(state["artifacts"])
        if handlers is not None and phase in handlers:
            produced = handlers[phase](state)
            if produced is not None:
                artifacts.append(produced)
        return {
            "current_phase": phase,
            "completed_phases": [*state["completed_phases"], phase],
            "artifacts": artifacts,
        }

    return run_phase


def build_spiral_graph(
    handlers: Mapping[str, PhaseHandler] | None = None,
    checkpointer: Any | None = None,
) -> Any:
    """Compile the LangGraph spiral.

    One node per spiral phase; conditional routing (at entry and after each phase)
    selects the next active phase from ``phase_sequence`` or ends. ``handlers`` and
    ``checkpointer`` are injected by the application composition root, keeping the
    workflow free of concrete infrastructure. Returns a compiled LangGraph runnable.
    """

    builder = StateGraph(SpiralState)
    for phase in SPIRAL_PHASES:
        # langgraph's heavily-overloaded add_node does not accept a dynamically built
        # partial-update node under mypy --strict; run_phase returns a valid partial
        # state dict at runtime (verified by tests).
        builder.add_node(phase, _make_phase_node(phase, handlers))  # type: ignore[call-overload]

    route_map: dict[Hashable, str] = {phase: phase for phase in SPIRAL_PHASES}
    route_map[_END] = _END

    builder.add_conditional_edges(START, next_active_phase, route_map)
    for phase in SPIRAL_PHASES:
        builder.add_conditional_edges(phase, next_active_phase, route_map)

    return builder.compile(checkpointer=checkpointer)
