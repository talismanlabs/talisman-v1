"""The Gate domain model.

A gate is a point in the project spiral where work pauses for a human decision
(for example ``interview``, ``plan``, ``slice_approval``, ``review``). The domain
models only the gate's identity and decision state; how a gate is presented and
approved (Telegram, a future dashboard) lives in adapters, not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GateStatus(str, Enum):
    """Lifecycle state of an approval gate."""

    PENDING = "pending"
    APPROVED = "approved"
    REVISE = "revise"
    PAUSED = "paused"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Gate:
    """Immutable description of an approval gate within a project spiral."""

    gate_id: str
    project_id: str
    name: str
    status: GateStatus
