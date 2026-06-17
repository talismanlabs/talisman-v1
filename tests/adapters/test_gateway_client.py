"""Tests for the gateway client adapter (slice S09.01)."""

import httpx

from talisman_core.adapters.gateway_client import GatewayClient
from talisman_core.ports.gateway import GatewayMessage, GatewayRequest, GatewayResult


def _request() -> GatewayRequest:
    return GatewayRequest(
        provider="anthropic",
        model="claude-opus",
        task_profile="routine",
        messages=(GatewayMessage(role="user", content="hi"),),
    )


def test_client_routes_through_injected_transport() -> None:
    """submit_model_request delegates to the injected transport (the gateway port)."""
    expected = GatewayResult(
        provider="anthropic",
        model="claude-opus",
        content="ok",
        prompt_tokens=1,
        completion_tokens=2,
        cost_usd=0.01,
    )
    seen: dict[str, GatewayRequest] = {}

    def transport(request: GatewayRequest) -> GatewayResult:
        seen["request"] = request
        return expected

    result = GatewayClient(transport).submit_model_request(_request())
    assert result is expected
    assert seen["request"].provider == "anthropic"


def test_http_transport_posts_to_gateway(monkeypatch) -> None:
    """The HTTP transport POSTs to /v1/model with the secret header and parses the result."""
    captured: dict[str, object] = {}

    class _Response:
        def raise_for_status(self) -> None: ...

        def json(self) -> dict[str, object]:
            return {
                "provider": "anthropic",
                "model": "claude-opus",
                "content": "hello",
                "prompt_tokens": 3,
                "completion_tokens": 4,
                "cost_usd": 0.05,
            }

    def fake_post(url, headers, json, timeout):
        captured.update(url=url, headers=headers, json=json)
        return _Response()

    monkeypatch.setattr(httpx, "post", fake_post)
    client = GatewayClient.over_http("http://127.0.0.1:8787/", "shh")
    result = client.submit_model_request(_request())

    assert captured["url"] == "http://127.0.0.1:8787/v1/model"
    assert captured["headers"]["X-Talisman-Gateway-Secret"] == "shh"  # type: ignore[index]
    assert captured["json"]["messages"] == [{"role": "user", "content": "hi"}]  # type: ignore[index]
    assert result.content == "hello"
    assert result.cost_usd == 0.05
