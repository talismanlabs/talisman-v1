"""Model gateway port for provider-neutral language model requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GatewayMessage:
    """One provider-neutral message sent through the model gateway."""

    role: str
    content: str


@dataclass(frozen=True)
class GatewayRequest:
    """Provider-neutral model request submitted through the TalisMan gateway."""

    provider: str
    model: str
    task_profile: str
    messages: tuple[GatewayMessage, ...]
    estimated_cost_usd: float = 0.0
    max_tokens: int = 4096


@dataclass(frozen=True)
class GatewayResult:
    """Normalized model result returned by the TalisMan gateway."""

    provider: str
    model: str
    content: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


class GatewayPort(Protocol):
    """Interface for submitting model requests through the budget gateway."""

    def submit_model_request(self, request: GatewayRequest) -> GatewayResult:
        """Submit a model request and return the normalized gateway result."""
        ...
