"""Telegram approval channel (v1.1 — live-telegram; AT-05).

Resolves each governed-spiral gate through Telegram: posts the gate to the operator, then blocks
until the operator replies APPROVE or REJECT. Implements ``ApprovalPort``, so the orchestrator
depends only on the port — the live transport (``TelegramBot``) is injected.

A gate guards real, sometimes irreversible action, so acceptance is deliberately strict:

- **Fresh reply only.** Pending updates from before the gate are drained first, so a stale reply
  cannot resolve a new gate (only a reply that arrives after the gate is posted counts).
- **Operator chat only.** A reply must come from the configured operator ``chat_id`` — an
  allowlisted user's message in some other chat is ignored.
- **Allowlisted sender only**, and only the exact words **APPROVE / REJECT** (case-insensitive,
  optional leading ``/``) — ambiguous tokens are not treated as a decision.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from talisman_core.adapters.telegram.bot import TelegramBot
from talisman_core.ports.approval import ApprovalDecision, ApprovalRequest


def _parse_decision(text: str) -> ApprovalDecision | None:
    """Map a reply to a decision — only the exact APPROVE/REJECT commands, else ``None``."""
    word = text.strip().lower().lstrip("/").strip()
    if word == "approve":
        return ApprovalDecision.APPROVE
    if word == "reject":
        return ApprovalDecision.REJECT
    return None


class TelegramApprover:
    """Resolve gates through Telegram (operator-chat, allowlisted approve/reject). ``ApprovalPort``."""

    def __init__(
        self,
        bot: TelegramBot,
        chat_id: int,
        *,
        poll_timeout_seconds: int = 30,
        poll_interval_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Bind the approver to a bot + operator chat. ``sleep`` is injected for tests."""
        self._bot = bot
        self._chat_id = chat_id
        self._poll_timeout = poll_timeout_seconds
        self._poll_interval = poll_interval_seconds
        self._sleep = sleep
        self._offset = 0

    def request_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        """Post the gate and block until a fresh, operator-chat, allowlisted APPROVE/REJECT.

        A gate is a deliberate pause: this waits for the human. Stale (pre-gate) replies, replies
        from other chats or non-allowlisted users, and anything that is not exactly APPROVE/REJECT
        are all ignored.
        """
        self._drain_pending_updates()
        self._bot.send_message(
            self._chat_id,
            f"TalisMan gate: {request.gate_id}\n{request.message}\n\nReply APPROVE or REJECT.",
        )
        while True:
            for message in self._bot.get_updates(
                offset=self._offset, timeout_seconds=self._poll_timeout
            ):
                self._offset = message.update_id + 1
                if message.chat_id != self._chat_id:
                    continue
                if not self._bot.is_authorized(message):
                    continue
                decision = _parse_decision(message.text)
                if decision is not None:
                    return decision
            self._sleep(self._poll_interval)

    def _drain_pending_updates(self) -> None:
        """Advance the cursor past every update that exists before the gate is posted."""
        while True:
            pending = self._bot.get_updates(offset=self._offset, timeout_seconds=0)
            if not pending:
                break
            self._offset = pending[-1].update_id + 1
