"""Tests for the gateway client adapter (slice S09.01; full-jitter retry S16.08)."""

import httpx
import pytest

from talisman_core.adapters.gateway_client import GatewayClient, retrying_transport
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


# --- Full-jitter retry on transient gateway failures (S16.08, AT-12) ---


def _ok_result() -> GatewayResult:
    return GatewayResult(
        provider="anthropic",
        model="claude-opus",
        content="ok",
        prompt_tokens=1,
        completion_tokens=1,
        cost_usd=0.0,
    )


def _status_error(code: int, retry_after: str | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "http://gw/v1/model")
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    response = httpx.Response(code, headers=headers, request=request)
    return httpx.HTTPStatusError(f"status {code}", request=request, response=response)


def test_retries_transient_transport_error_then_succeeds() -> None:
    """A transport error (e.g. a dropped connection) is retried, not fatal."""
    calls = {"n": 0}

    def inner(request: GatewayRequest) -> GatewayResult:
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ConnectError("blip")
        return _ok_result()

    slept: list[float] = []
    transport = retrying_transport(inner, sleep=slept.append, rand=lambda: 0.5)

    assert transport(_request()).content == "ok"
    assert calls["n"] == 3
    assert len(slept) == 2  # two backoffs before the third, successful attempt


def test_does_not_retry_a_client_error() -> None:
    """A non-retryable 4xx (e.g. 400) surfaces immediately — no retry, no sleep."""

    def inner(request: GatewayRequest) -> GatewayResult:
        raise _status_error(400)

    slept: list[float] = []
    transport = retrying_transport(inner, sleep=slept.append, rand=lambda: 0.5)

    with pytest.raises(httpx.HTTPStatusError):
        transport(_request())
    assert slept == []


def test_honors_numeric_retry_after_on_429() -> None:
    """A 429 with a numeric Retry-After waits exactly that long before retrying."""
    calls = {"n": 0}

    def inner(request: GatewayRequest) -> GatewayResult:
        calls["n"] += 1
        if calls["n"] == 1:
            raise _status_error(429, retry_after="7")
        return _ok_result()

    slept: list[float] = []
    transport = retrying_transport(inner, sleep=slept.append, rand=lambda: 0.5)

    assert transport(_request()).content == "ok"
    assert slept == [7.0]


def test_exhausts_attempts_then_raises() -> None:
    """Persistent 5xx is retried up to max_attempts, then the error propagates."""

    def inner(request: GatewayRequest) -> GatewayResult:
        raise _status_error(503)

    slept: list[float] = []
    transport = retrying_transport(inner, max_attempts=3, sleep=slept.append, rand=lambda: 0.5)

    with pytest.raises(httpx.HTTPStatusError):
        transport(_request())
    assert len(slept) == 2  # max_attempts - 1 backoffs, then raise


def test_full_jitter_delay_never_exceeds_the_cap() -> None:
    """Even at worst-case jitter the backoff is bounded by max_delay."""

    def inner(request: GatewayRequest) -> GatewayResult:
        raise httpx.ConnectError("blip")

    slept: list[float] = []
    transport = retrying_transport(
        inner, max_attempts=8, base_delay=1.0, max_delay=5.0, sleep=slept.append, rand=lambda: 1.0
    )

    with pytest.raises(httpx.ConnectError):
        transport(_request())
    assert slept  # some backoffs happened
    assert max(slept) == 5.0  # reaches but never exceeds the cap
    assert all(d <= 5.0 for d in slept)


def test_retries_all_5xx_not_just_a_fixed_set() -> None:
    """Any 5xx (e.g. 501, 520, 599) is retried, not only the common ones (429/5xx claim)."""
    for status in (501, 520, 599):
        calls = {"n": 0}

        def inner(request: GatewayRequest, _status: int = status) -> GatewayResult:
            calls["n"] += 1
            if calls["n"] == 1:
                raise _status_error(_status)
            return _ok_result()

        slept: list[float] = []
        transport = retrying_transport(inner, sleep=slept.append, rand=lambda: 0.5)
        assert transport(_request()).content == "ok"
        assert len(slept) == 1, f"status {status} should have been retried"


def test_retry_after_above_cap_is_honored_not_truncated() -> None:
    """A server Retry-After larger than max_delay is honored as-is (a minimum, not capped)."""
    calls = {"n": 0}

    def inner(request: GatewayRequest) -> GatewayResult:
        calls["n"] += 1
        if calls["n"] == 1:
            raise _status_error(503, retry_after="60")
        return _ok_result()

    slept: list[float] = []
    transport = retrying_transport(inner, max_delay=30.0, sleep=slept.append, rand=lambda: 0.5)

    assert transport(_request()).content == "ok"
    assert slept == [60.0]  # not truncated to max_delay
