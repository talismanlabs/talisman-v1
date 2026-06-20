"""Gateway client adapter (slice S09.01).

Routes provider-neutral model requests through the host-side gateway via the typed
``GatewayPort``. Per ADR-0004 the gateway forwards directly to providers (no LiteLLM);
this client only ever talks to the gateway, never a provider. The transport is
injected so the adapter is testable without a live gateway, the network, or any
provider call.
"""

from __future__ import annotations

import random
import time
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


def _is_retryable_status(status: int) -> bool:
    """Retry rate-limiting (429) and any transient server error (5xx); other 4xx are client
    errors that must surface immediately rather than being retried."""
    return status == 429 or 500 <= status <= 599


def _retry_after_seconds(response: httpx.Response) -> float | None:
    """Parse a numeric Retry-After header (seconds); the HTTP-date form is ignored."""
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def retrying_transport(
    inner: GatewayTransport,
    *,
    max_attempts: int = 4,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    sleep: Callable[[float], None] = time.sleep,
    rand: Callable[[], float] = random.random,
) -> GatewayTransport:
    """Wrap a transport with full-jitter retry on transient gateway failures.

    Retries transport errors and 429 / any 5xx responses up to ``max_attempts`` with
    full-jitter exponential backoff capped at ``max_delay``; a numeric Retry-After is honored
    as a MINIMUM delay (never truncated below the header value). Any non-retryable status
    (e.g. a 4xx other than 429) propagates immediately, so a transient blip cannot kill an
    unattended run while a real error still surfaces. ``sleep`` and ``rand`` are injected so
    the backoff is deterministic under test.
    """
    if max_attempts < 1:
        message = "max_attempts must be >= 1"
        raise ValueError(message)

    def transport(request: GatewayRequest) -> GatewayResult:
        attempt = 1
        while True:
            retry_after: float | None = None
            try:
                return inner(request)
            except httpx.HTTPStatusError as exc:
                if not _is_retryable_status(exc.response.status_code) or attempt >= max_attempts:
                    raise
                retry_after = _retry_after_seconds(exc.response)
            except httpx.TransportError:
                if attempt >= max_attempts:
                    raise
            # Full-jitter exponential backoff, capped at max_delay; but a server-directed
            # Retry-After is honored as a MINIMUM and never truncated below the header value.
            capped = min(max_delay, base_delay * (2.0 ** (attempt - 1)))
            delay = retry_after if retry_after is not None else rand() * capped
            sleep(delay)
            attempt += 1

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
        """Build a client that talks to the host-side gateway over HTTP, with full-jitter
        retry on transient failures so a blip cannot kill an unattended run."""
        return cls(retrying_transport(http_transport(base_url, gateway_secret)))

    def submit_model_request(self, request: GatewayRequest) -> GatewayResult:
        """Route the request through the gateway transport and return its result."""
        return self._transport(request)
