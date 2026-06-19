"""Application composition root (slice S14.01).

The composition root is the ONE place allowed to wire concrete implementations together
(guardrail: app_is_composition_root). It assembles the LangGraph spiral, an in-memory
checkpointer, the portfolio scheduler, and structured logging into a runnable
``TalismanApp`` behind ``talisman_core.main``. Per ADR-0005 this slice supplies
deterministic phase handlers; worker-driven handlers and the governed v1.1 run arrive in
S14.02, injected through the same seams with no change to this wiring.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, cast

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from talisman_core.observability.logs import StructuredLogger
from talisman_core.ports.approval import ApprovalPort, ApprovalRequest
from talisman_core.scheduler.portfolio import PortfolioScheduler
from talisman_core.workflow.spiral import (
    SPIRAL_PHASES,
    PhaseHandler,
    SpiralState,
    build_spiral_graph,
)


def _stdout_sink(line: str) -> None:
    """Default log sink: write the already-newline-terminated line to stdout (journald)."""
    sys.stdout.write(line)


def default_phase_handlers() -> dict[str, PhaseHandler]:
    """Deterministic phase handlers: each phase records one reproducible artifact.

    Real, worker-driven handlers are wired in S14.02; these make the assembled spiral
    runnable and testable without any live worker, gateway, or API spend.
    """

    def make(phase: str) -> PhaseHandler:
        def handle(state: SpiralState) -> str:
            return f"{phase}:{state['project_id']}"

        return handle

    return {phase: make(phase) for phase in SPIRAL_PHASES}


@dataclass
class TalismanApp:
    """An assembled, runnable TalisMan orchestrator."""

    graph: Any
    scheduler: PortfolioScheduler
    logger: StructuredLogger
    gate_phases: frozenset[str]

    def run_project(
        self,
        project_id: str,
        phase_sequence: list[str],
        tier: str = "standard",
    ) -> SpiralState:
        """Run one project spiral to completion and return the final state.

        Intended for the deterministic (non-gated) cycle; gated governance with
        interrupt/resume is exercised in S14.02.
        """

        initial: SpiralState = {
            "project_id": project_id,
            "tier": tier,
            "phase_sequence": phase_sequence,
            "current_phase": "",
            "completed_phases": [],
            "pending_gate_id": None,
            "last_decision": None,
            "artifacts": [],
            "escalations_today": 0,
        }
        self.logger.log("project_started", project_id=project_id, phases=phase_sequence)
        config = {"configurable": {"thread_id": project_id}}
        final = cast(SpiralState, self.graph.invoke(initial, config=config))
        self.logger.log(
            "project_finished",
            project_id=project_id,
            completed=final["completed_phases"],
            artifacts=final["artifacts"],
        )
        return final

    def run_gated_project(
        self,
        project_id: str,
        phase_sequence: list[str],
        approver: ApprovalPort,
        tier: str = "standard",
    ) -> SpiralState:
        """Run a gated project spiral, resolving each gate through the approval port.

        The spiral runs until it interrupts at a gate; the interrupt payload is turned
        into an ``ApprovalRequest``, the approver decides, and the graph resumes with
        that decision. The loop repeats until the spiral completes (or a reject ends it).
        """

        initial: SpiralState = {
            "project_id": project_id,
            "tier": tier,
            "phase_sequence": phase_sequence,
            "current_phase": "",
            "completed_phases": [],
            "pending_gate_id": None,
            "last_decision": None,
            "artifacts": [],
            "escalations_today": 0,
        }
        config = {"configurable": {"thread_id": project_id}}
        self.logger.log("gated_project_started", project_id=project_id, phases=phase_sequence)
        result = self.graph.invoke(initial, config=config)
        while "__interrupt__" in result:
            payload = result["__interrupt__"][0].value
            request = ApprovalRequest(
                project_id=payload["project_id"],
                gate_id=payload["gate_id"],
                message=payload["summary"],
                idempotency_key=payload["gate_id"],
            )
            decision = approver.request_approval(request)
            result = self.graph.invoke(Command(resume=decision.value), config=config)
        final = cast(SpiralState, result)
        self.logger.log(
            "gated_project_finished",
            project_id=project_id,
            completed=final["completed_phases"],
            artifacts=final["artifacts"],
        )
        return final


def build_application(
    *,
    handlers: Mapping[str, PhaseHandler] | None = None,
    checkpointer: Any | None = None,
    gate_phases: set[str] | None = None,
    log_sink: Callable[[str], Any] | None = None,
) -> TalismanApp:
    """Wire the orchestrator: spiral graph + checkpointer + scheduler + logging.

    Every dependency has a deterministic default, so the assembled app runs in-process
    with no live infrastructure (ADR-0005). Overrides exist for tests and for the
    worker-driven, governed run wired in S14.02.
    """

    resolved_handlers = dict(handlers) if handlers is not None else default_phase_handlers()
    resolved_checkpointer = checkpointer if checkpointer is not None else MemorySaver()
    resolved_gate_phases = frozenset(gate_phases or ())
    logger = StructuredLogger(log_sink or _stdout_sink)
    graph = build_spiral_graph(
        handlers=resolved_handlers,
        checkpointer=resolved_checkpointer,
        gate_phases=set(resolved_gate_phases),
    )
    return TalismanApp(
        graph=graph,
        scheduler=PortfolioScheduler(),
        logger=logger,
        gate_phases=resolved_gate_phases,
    )
