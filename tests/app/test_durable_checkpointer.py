"""Durable-checkpointer test (slice S16.07, AT-04).

Proves a paused gate run survives a process restart: a graph paused under one SqliteSaver
is recovered by a FRESH SqliteSaver opened on the SAME on-disk database — which the
in-memory MemorySaver cannot do. This is exactly the durability the AT-04 waiver was about.
"""

from __future__ import annotations

from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from talisman_core.app.composition import build_sqlite_checkpointer
from talisman_core.ports.approval import ApprovalDecision
from talisman_core.workflow.spiral import SpiralState, build_spiral_graph


def _state() -> SpiralState:
    return {
        "project_id": "p1",
        "tier": "full_spiral",
        "phase_sequence": ["interview", "plan", "review"],
        "current_phase": "",
        "completed_phases": [],
        "pending_gate_id": None,
        "last_decision": None,
        "artifacts": [],
        "escalations_today": 0,
    }


def _config() -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": "p1"}}


def test_paused_gate_resumes_after_a_fresh_checkpointer_restart(tmp_path: Path) -> None:
    """A run paused at a gate under one checkpointer resumes correctly under a brand-new
    checkpointer on the same DB file — i.e., resume survives a process restart (AT-04)."""
    db = tmp_path / "state" / "talisman.db"
    config = _config()

    # Run 1: pause at the 'plan' gate. The checkpoint is written to the SQLite file.
    graph1 = build_spiral_graph(checkpointer=build_sqlite_checkpointer(db), gate_phases={"plan"})
    result = graph1.invoke(_state(), config)
    assert "__interrupt__" in result  # paused at the gate

    # "Restart": a brand-new checkpointer + graph on the SAME db (no shared in-memory state).
    graph2 = build_spiral_graph(checkpointer=build_sqlite_checkpointer(db), gate_phases={"plan"})

    # The paused state is recovered from disk — what MemorySaver cannot do.
    recovered = graph2.get_state(config)
    assert recovered.next == ("plan",)
    assert recovered.values["pending_gate_id"] == "p1:plan"
    assert recovered.values["completed_phases"] == ["interview"]

    # ...and resuming with an approval completes the run.
    final = graph2.invoke(Command(resume=ApprovalDecision.APPROVE.value), config)
    assert final["completed_phases"] == ["interview", "plan", "review"]
    assert graph2.get_state(config).next == ()


def test_memory_saver_loses_the_paused_run_on_restart_contrast(tmp_path: Path) -> None:
    """Contrast: a fresh in-memory saver has no recollection of the paused run, so the
    SqliteSaver durability above is real, not incidental."""
    config = _config()
    build_spiral_graph(checkpointer=MemorySaver(), gate_phases={"plan"}).invoke(_state(), config)

    # A brand-new MemorySaver ("restart") starts empty — the paused run is gone.
    restarted = build_spiral_graph(checkpointer=MemorySaver(), gate_phases={"plan"})
    assert restarted.get_state(config).next == ()  # nothing to resume — lost on restart
