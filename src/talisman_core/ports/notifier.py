"""User notification port for workflow status and action-required messages."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class NotificationLevel(str, Enum):
    """Severity level for a user notification."""

    INFO = "info"
    WARNING = "warning"
    ACTION_REQUIRED = "action_required"
    ERROR = "error"


@dataclass(frozen=True)
class Notification:
    """Notification message destined for the user-facing control plane."""

    title: str
    message: str
    level: NotificationLevel
    project_id: str | None = None
    idempotency_key: str | None = None


class NotifierPort(Protocol):
    """Interface for sending user-visible workflow notifications."""

    def send_notification(self, notification: Notification) -> None:
        """Send a notification to the user-facing control plane."""
        ...
