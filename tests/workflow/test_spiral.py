"""Tests for the LangGraph spiral workflow."""

from collections.abc import Mapping
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from talisman_core.ports.approval import ApprovalDecision

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


def _config(project_id: str = "p1") -> dict[str, dict[str, str]]:
    """Build a LangGraph config keyed by project id for checkpointed resumes."""
    return {"configurable": {"thread_id": project_id}}


def _interrupt_payload(result: Mapping[str, Any]) -> dict[str, str]:
    """Extract the first interrupt payload from a LangGraph invoke result."""
    interrupts = result["__interrupt__"]
    payload = interrupts[0].value
    assert isinstance(payload, dict)
    return payload


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


def test_gate_phase_interrupts_with_pending_gate_checkpoint() -> None:
    """A policy-injected gate pauses and stores the pending gate id in state."""
    graph = build_spiral_graph(checkpointer=MemorySaver(), gate_phases={"plan"})
    config = _config()
    initial = _state(["interview", "plan", "review"], [])

    result = graph.invoke(initial, config)

    payload = _interrupt_payload(result)
    assert payload == {
        "project_id": "p1",
        "gate_id": "p1:plan",
        "phase": "plan",
        "summary": "Approval required for phase 'plan'.",
    }
    snapshot = graph.get_state(config)
    assert snapshot.next == ("plan",)
    assert snapshot.values["pending_gate_id"] == "p1:plan"
    assert snapshot.values["completed_phases"] == ["interview"]


def test_resume_with_approve_advances_and_completes_sequence() -> None:
    """An approve decision completes the gated phase and advances to END."""
    graph = build_spiral_graph(checkpointer=MemorySaver(), gate_phases={"plan"})
    config = _config()
    initial = _state(["interview", "plan", "review"], [])

    graph.invoke(initial, config)
    final = graph.invoke(Command(resume=ApprovalDecision.APPROVE.value), config)

    assert final["completed_phases"] == ["interview", "plan", "review"]
    assert final["current_phase"] == "review"
    assert final["pending_gate_id"] is None
    assert final["last_decision"] == ApprovalDecision.APPROVE.value
    assert graph.get_state(config).next == ()


def test_resume_with_revise_reenters_current_phase() -> None:
    """A revise decision leaves the phase incomplete and runs it again."""
    run_count = 0

    def plan_handler(_state: SpiralState) -> str:
        nonlocal run_count
        run_count += 1
        return f"plan-artifact-{run_count}"

    graph = build_spiral_graph(
        handlers={"plan": plan_handler},
        checkpointer=MemorySaver(),
        gate_phases={"plan"},
    )
    config = _config()
    initial = _state(["interview", "plan", "review"], [])

    graph.invoke(initial, config)
    result = graph.invoke(Command(resume=ApprovalDecision.REVISE.value), config)

    payload = _interrupt_payload(result)
    snapshot = graph.get_state(config)
    assert payload["gate_id"] == "p1:plan"
    assert run_count == 2
    assert snapshot.next == ("plan",)
    assert snapshot.values["completed_phases"] == ["interview"]
    assert snapshot.values["pending_gate_id"] == "p1:plan"
    assert snapshot.values["last_decision"] == ApprovalDecision.REVISE.value
    assert snapshot.values["artifacts"] == ["plan-artifact-1", "plan-artifact-2"]


def test_resume_with_pause_stays_interrupted_at_gate() -> None:
    """A pause decision records the decision and remains interrupted at the gate."""
    graph = build_spiral_graph(checkpointer=MemorySaver(), gate_phases={"plan"})
    config = _config()
    initial = _state(["interview", "plan", "review"], [])

    graph.invoke(initial, config)
    result = graph.invoke(Command(resume=ApprovalDecision.PAUSE.value), config)

    payload = _interrupt_payload(result)
    snapshot = graph.get_state(config)
    assert payload["gate_id"] == "p1:plan"
    assert snapshot.next == ("plan",)
    assert snapshot.values["completed_phases"] == ["interview"]
    assert snapshot.values["pending_gate_id"] == "p1:plan"
    assert snapshot.values["last_decision"] == ApprovalDecision.PAUSE.value


def test_resume_with_reject_ends_early_without_completing_gate() -> None:
    """A reject decision routes to END without marking the gated phase complete."""
    graph = build_spiral_graph(checkpointer=MemorySaver(), gate_phases={"plan"})
    config = _config()
    initial = _state(["interview", "plan", "review"], [])

    graph.invoke(initial, config)
    final = graph.invoke(Command(resume=ApprovalDecision.REJECT.value), config)

    assert final["completed_phases"] == ["interview"]
    assert final["current_phase"] == "plan"
    assert final["pending_gate_id"] is None
    assert final["last_decision"] == ApprovalDecision.REJECT.value
    assert graph.get_state(config).next == ()
