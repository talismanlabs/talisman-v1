"""Typed interfaces (ports) for external capabilities.

Ports are ``typing.Protocol`` contracts for workers, approval, state, gateway,
memory, and notifications. They declare *what* the core needs without binding it to
*how* it is provided. Ports may define interfaces but must not import concrete
adapters.
"""

from talisman_core.ports.approval import ApprovalDecision, ApprovalPort, ApprovalRequest
from talisman_core.ports.gateway import GatewayMessage, GatewayPort, GatewayRequest, GatewayResult
from talisman_core.ports.memory import (
    Lesson,
    LessonQuery,
    LessonSeverity,
    LessonStatus,
    MemoryPort,
    Retrospective,
)
from talisman_core.ports.notifier import Notification, NotificationLevel, NotifierPort
from talisman_core.ports.state import GateEvent, StatePort
from talisman_core.ports.worker import WorkerPort, WorkerRequest, WorkerResult

__all__ = [
    "ApprovalDecision",
    "ApprovalPort",
    "ApprovalRequest",
    "GateEvent",
    "GatewayMessage",
    "GatewayPort",
    "GatewayRequest",
    "GatewayResult",
    "Lesson",
    "LessonQuery",
    "LessonSeverity",
    "LessonStatus",
    "MemoryPort",
    "Notification",
    "NotificationLevel",
    "NotifierPort",
    "Retrospective",
    "StatePort",
    "WorkerPort",
    "WorkerRequest",
    "WorkerResult",
]
