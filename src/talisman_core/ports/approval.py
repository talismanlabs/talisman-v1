"""Human approval port for irreversible or gated workflow decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ApprovalDecision(str, Enum):
    """Possible user decisions at a human approval gate."""

    APPROVE = "approve"
    REVISE = "revise"
    PAUSE = "pause"
    REJECT = "reject"


@dataclass(frozen=True)
class ApprovalRequest:
    """Approval request shown to the user through an interface adapter."""

    project_id: str
    gate_id: str
    message: str
    idempotency_key: str


class ApprovalPort(Protocol):
    """Interface for human approval systems such as Telegram or a future dashboard."""

    def request_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        """Ask the user for a decision and return the normalized response."""
        ...
