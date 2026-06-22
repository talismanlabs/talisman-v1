"""Telegram bot runtime (v1.1 — live-telegram).

Reads the bot token and the allowlist from operator secret files, connects to the
Telegram Bot API over httpx, and enforces the S05.01 allowlist on every inbound
command: a message from a non-allowlisted user is rejected (and logged by the caller)
before any action is taken. The allowlist membership logic itself lives in
``adapters.telegram.allowlist``; this module is the live transport around it.

The bot token lives in the request URL (Telegram's API shape). httpx exception messages
include the full URL, so a transport failure could otherwise carry ``bot<TOKEN>`` into logs
or an incident dump. Every request therefore goes through ``_request``, which catches httpx
errors and re-raises a ``TelegramTransportError`` with the token scrubbed and the original
(token-bearing) exception suppressed — the token never escapes this module in an exception.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from talisman_core.adapters.telegram.allowlist import TelegramAllowlist, load_allowlist


class TelegramTransportError(RuntimeError):
    """A Telegram API failure, with the bot token scrubbed from the message."""


@dataclass(frozen=True)
class IncomingMessage:
    """A parsed inbound Telegram text message."""

    update_id: int
    user_id: int
    chat_id: int
    text: str


def _read_secret(path: Path) -> str:
    """Read and strip a single-value secret file (token)."""
    return path.read_text(encoding="utf-8").strip()


class TelegramBot:
    """A minimal Telegram control-plane runtime that enforces the user allowlist."""

    def __init__(
        self,
        token: str,
        allowlist: TelegramAllowlist,
        *,
        base_url: str = "https://api.telegram.org",
    ) -> None:
        """Build a bot bound to a token and an allowlist (base_url is injectable for tests)."""
        self._token = token
        self._base = f"{base_url}/bot{token}"
        self._allowlist = allowlist

    @classmethod
    def from_secret_files(cls, token_file: Path, allowlist_file: Path) -> TelegramBot:
        """Construct the bot from the operator's gitignored secret files."""
        return cls(_read_secret(token_file), load_allowlist(allowlist_file))

    def _scrub(self, text: str) -> str:
        """Remove the bot token from a string before it can be surfaced or persisted."""
        return text.replace(self._token, "[REDACTED]") if self._token else text

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Issue a Telegram API request, scrubbing the bot token from any failure."""
        url = f"{self._base}/{path}"
        try:
            response = httpx.get(url, **kwargs) if method == "get" else httpx.post(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:
            raise TelegramTransportError(self._scrub(str(exc))) from None

    def get_me(self) -> dict[str, Any]:
        """Call getMe to confirm the token is valid and Telegram is reachable."""
        response = self._request("get", "getMe", timeout=15)
        result: dict[str, Any] = response.json()["result"]
        return result

    def get_updates(self, offset: int = 0, timeout_seconds: int = 0) -> list[IncomingMessage]:
        """Long-poll getUpdates and return parsed text messages."""
        response = self._request(
            "get",
            "getUpdates",
            params={"offset": offset, "timeout": timeout_seconds},
            timeout=timeout_seconds + 10,
        )
        messages: list[IncomingMessage] = []
        for update in response.json()["result"]:
            message = update.get("message")
            if message is None or "text" not in message:
                continue
            messages.append(
                IncomingMessage(
                    update_id=update["update_id"],
                    user_id=message["from"]["id"],
                    chat_id=message["chat"]["id"],
                    text=message["text"],
                )
            )
        return messages

    def send_message(self, chat_id: int, text: str) -> None:
        """Send a text reply to a chat."""
        self._request("post", "sendMessage", json={"chat_id": chat_id, "text": text}, timeout=15)

    def is_authorized(self, message: IncomingMessage) -> bool:
        """Return True only if the message's sender is on the allowlist (S05.01)."""
        return self._allowlist.is_allowed(message.user_id)
