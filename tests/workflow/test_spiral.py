"""Tests for the LangGraph spiral workflow (slice S03.01)."""

from talisman_core.workflow.spiral import (
    SPIRAL_PHASES,
    SpiralState,
    build_spiral_graph,
    next_active_phase,
)


def _state(phase_sequence: list[str], completed: list[str]) -> SpiralState:
    """Build a SpiralState for tests with the given sequence/completed phases."""
    return {
        "project_id": "p1",
        "tier": "full_spiral",
        "phase_sequence": phase_sequence,
        "current_phase": completed[-1] if completed else "",
        "completed_phases": completed,
        "pending_gate_id": None,
        "last_decision": None,
        "artifacts": [],
        "escalations_today": 0,
    }


def test_next_active_phase_returns_first_uncompleted_in_sequence() -> None:
    """Routing picks the next phase in the sequence that is not yet completed."""
    assert next_active_phase(_state(["interview", "plan", "review"], ["interview"])) == "plan"


def test_next_active_phase_returns_end_when_exhausted() -> None:
    """When every active phase is completed, routing ends the graph."""
    assert next_active_phase(_state(["interview", "plan"], ["interview", "plan"])) == "__end__"


def test_graph_compiles_and_walks_lightweight_sequence_to_end() -> None:
    """A lightweight phase_sequence runs to completion, skipping inactive phases."""
    graph = build_spiral_graph()
    initial = _state(["interview", "plan", "slice_approval", "review", "retro"], [])
    final = graph.invoke(initial)
    assert final["completed_phases"] == ["interview", "plan", "slice_approval", "review", "retro"]
    assert final["current_phase"] == "retro"
    # discovery and red_team are not in the sequence, so they are never entered.
    assert "discovery" not in final["completed_phases"]


def test_graph_walks_full_spiral_through_all_nine_phases() -> None:
    """The full spiral runs every canonical phase in order."""
    graph = build_spiral_graph()
    initial = _state(list(SPIRAL_PHASES), [])
    final = graph.invoke(initial)
    assert final["completed_phases"] == list(SPIRAL_PHASES)


def test_injected_handler_records_artifact() -> None:
    """A phase handler may produce an artifact id, which the node records."""
    graph = build_spiral_graph(handlers={"plan": lambda _state: "plan-artifact-1"})
    initial = _state(["interview", "plan", "retro"], [])
    final = graph.invoke(initial)
    assert "plan-artifact-1" in final["artifacts"]
