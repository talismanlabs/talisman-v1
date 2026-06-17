"""Gateway client adapter (slice S09.01).

Routes provider-neutral model requests through the host-side gateway via the typed
``GatewayPort``. Per ADR-0004 the gateway forwards directly to providers (no LiteLLM);
this client only ever talks to the gateway, never a provider. The transport is
injected so the adapter is testable without a live gateway, the network, or any
provider call.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx

from talisman_core.ports.gateway import GatewayRequest, GatewayResult

# A transport carries a GatewayRequest to the gateway service and returns its result.
GatewayTransport = Callable[[GatewayRequest], GatewayResult]


def _result_from_payload(payload: Any) -> GatewayResult:
    """Build a GatewayResult from the gateway service's JSON response body."""
    return GatewayResult(
        provider=str(payload["provider"]),
        model=str(payload["model"]),
        content=str(payload["content"]),
        prompt_tokens=int(payload["prompt_tokens"]),
        completion_tokens=int(payload["completion_tokens"]),
        cost_usd=float(payload["cost_usd"]),
    )


def http_transport(base_url: str, gateway_secret: str) -> GatewayTransport:
    """Build a transport that POSTs requests to the host-side gateway over HTTP."""
    url = f"{base_url.rstrip('/')}/v1/model"

    def transport(request: GatewayRequest) -> GatewayResult:
        response = httpx.post(
            url,
            headers={"X-Talisman-Gateway-Secret": gateway_secret},
            json={
                "provider": request.provider,
                "model": request.model,
                "task_profile": request.task_profile,
                "max_tokens": request.max_tokens,
                "estimated_cost_usd": request.estimated_cost_usd,
                "messages": [
                    {"role": message.role, "content": message.content}
                    for message in request.messages
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        return _result_from_payload(response.json())

    return transport


class GatewayClient:
    """Submit model requests through the TalisMan gateway (implements ``GatewayPort``).

    The orchestrator depends only on ``GatewayPort``; this adapter carries the request
    to the gateway through an injected transport and never imports a provider SDK.
    """

    def __init__(self, transport: GatewayTransport) -> None:
        """Store the injected transport that carries requests to the gateway."""
        self._transport = transport

    @classmethod
    def over_http(cls, base_url: str, gateway_secret: str) -> GatewayClient:
        """Build a client that talks to the host-side gateway service over HTTP."""
        return cls(http_transport(base_url, gateway_secret))

    def submit_model_request(self, request: GatewayRequest) -> GatewayResult:
        """Route the request through the gateway transport and return its result."""
        return self._transport(request)
