"""Tests for the Telegram bot transport (slice S16.17)."""

from __future__ import annotations

import httpx
import pytest

from talisman_core.adapters.telegram.allowlist import TelegramAllowlist
from talisman_core.adapters.telegram.bot import (
    IncomingMessage,
    TelegramBot,
    TelegramTransportError,
)


def _bot(allowed: frozenset[int] = frozenset()) -> TelegramBot:
    return TelegramBot("TOKEN", TelegramAllowlist(allowed), base_url="http://tg.test")


def test_get_updates_parses_text_messages_and_skips_the_rest(monkeypatch) -> None:
    """getUpdates returns only parsed text messages; non-text / non-message updates are skipped."""
    payload = {
        "result": [
            {"update_id": 10, "message": {"from": {"id": 1}, "chat": {"id": 5}, "text": "approve"}},
            {"update_id": 11, "message": {"from": {"id": 2}, "chat": {"id": 6}}},  # no text
            {"update_id": 12},  # no message
        ]
    }

    class _Resp:
        def raise_for_status(self) -> None: ...

        def json(self) -> dict[str, object]:
            return payload

    monkeypatch.setattr(httpx, "get", lambda url, params=None, timeout=None: _Resp())

    messages = _bot().get_updates()

    assert [m.text for m in messages] == ["approve"]
    assert messages[0].user_id == 1
    assert messages[0].chat_id == 5
    assert messages[0].update_id == 10


def test_send_message_posts_chat_and_text(monkeypatch) -> None:
    """send_message POSTs to the bot's sendMessage endpoint with the chat id and text."""
    captured: dict[str, object] = {}

    class _Resp:
        def raise_for_status(self) -> None: ...

    def fake_post(url, json=None, timeout=None):
        captured.update(url=url, json=json)
        return _Resp()

    monkeypatch.setattr(httpx, "post", fake_post)

    _bot().send_message(123, "hello")

    assert captured["url"] == "http://tg.test/botTOKEN/sendMessage"
    assert captured["json"] == {"chat_id": 123, "text": "hello"}


def test_is_authorized_enforces_the_allowlist() -> None:
    """is_authorized is True only for a sender on the allowlist (S05.01)."""
    bot = _bot(frozenset({7}))
    assert bot.is_authorized(IncomingMessage(update_id=1, user_id=7, chat_id=5, text="hi")) is True
    assert bot.is_authorized(IncomingMessage(update_id=1, user_id=8, chat_id=5, text="hi")) is False


def test_a_transport_failure_does_not_leak_the_token(monkeypatch) -> None:
    """An httpx failure (whose message carries the token URL) re-raises with the token scrubbed."""
    token = "TESTTOKEN-fake-value-123"  # not a real token; the URL embeds it as Telegram does
    url = f"http://tg.test/bot{token}/getUpdates"

    class _Resp:
        def raise_for_status(self) -> None:
            request = httpx.Request("GET", url)
            raise httpx.HTTPStatusError(
                f"Server error '500' for url '{url}'",
                request=request,
                response=httpx.Response(500, request=request),
            )

    monkeypatch.setattr(httpx, "get", lambda u, params=None, timeout=None: _Resp())
    bot = TelegramBot(token, TelegramAllowlist(frozenset()), base_url="http://tg.test")

    with pytest.raises(TelegramTransportError) as excinfo:
        bot.get_updates()

    assert token not in str(excinfo.value)  # the token never surfaces in the raised error
    assert "[REDACTED]" in str(excinfo.value)
