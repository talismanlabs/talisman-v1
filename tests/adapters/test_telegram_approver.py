"""Tests for the Telegram approval channel (slice S16.17; AT-05)."""

from __future__ import annotations

from talisman_core.adapters.telegram.approver import TelegramApprover
from talisman_core.adapters.telegram.bot import IncomingMessage
from talisman_core.ports.approval import ApprovalDecision, ApprovalRequest

_OPERATOR_CHAT = 42


class _FakeBot:
    """Models Telegram offset semantics: ``get_updates`` returns updates with id >= offset.

    ``pre_gate`` updates exist before the gate is posted (they should be drained); ``post_gate``
    updates only appear after ``send_message`` is called. The approver — not this bot — enforces
    the operator chat and the allowlist.
    """

    def __init__(
        self,
        pre_gate: list[IncomingMessage],
        post_gate: list[IncomingMessage],
        allowed_users: set[int],
    ) -> None:
        self.sent: list[tuple[int, str]] = []
        self._pre = list(pre_gate)
        self._post = list(post_gate)
        self._allowed = allowed_users
        self._posted = False

    def send_message(self, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))
        self._posted = True

    def get_updates(self, offset: int = 0, timeout_seconds: int = 0) -> list[IncomingMessage]:
        pool = self._pre + (self._post if self._posted else [])
        return [m for m in pool if m.update_id >= offset]

    def is_authorized(self, message: IncomingMessage) -> bool:
        return message.user_id in self._allowed


def _msg(
    user_id: int, text: str, *, update_id: int, chat_id: int = _OPERATOR_CHAT
) -> IncomingMessage:
    return IncomingMessage(update_id=update_id, user_id=user_id, chat_id=chat_id, text=text)


def _req() -> ApprovalRequest:
    return ApprovalRequest(
        project_id="news-replica",
        gate_id="plan",
        message="approve the plan?",
        idempotency_key="plan",
    )


def _approver(bot: _FakeBot) -> TelegramApprover:
    return TelegramApprover(bot, chat_id=_OPERATOR_CHAT, sleep=lambda _s: None)  # type: ignore[arg-type]


def test_posts_the_gate_and_approves_on_an_allowlisted_operator_approve() -> None:
    """The gate is posted and a fresh, operator-chat, allowlisted APPROVE resolves it."""
    bot = _FakeBot([], [_msg(1, "approve", update_id=1)], allowed_users={1})

    decision = _approver(bot).request_approval(_req())

    assert decision is ApprovalDecision.APPROVE
    assert bot.sent and "plan" in bot.sent[0][1]  # the gate was posted to the operator


def test_rejects_on_an_allowlisted_reject() -> None:
    """An allowlisted REJECT resolves the gate as a rejection."""
    bot = _FakeBot([], [_msg(1, "reject", update_id=1)], allowed_users={1})
    assert _approver(bot).request_approval(_req()) is ApprovalDecision.REJECT


def test_a_stale_pre_gate_approval_is_ignored() -> None:
    """An allowlisted APPROVE that arrived BEFORE the gate must not resolve it (R1: no replay)."""
    bot = _FakeBot(
        [_msg(1, "approve", update_id=1)],  # stale, pre-gate
        [_msg(1, "reject", update_id=2)],  # the actual fresh reply
        allowed_users={1},
    )
    assert _approver(bot).request_approval(_req()) is ApprovalDecision.REJECT


def test_a_reply_from_another_chat_is_ignored() -> None:
    """An allowlisted user's approve in a DIFFERENT chat must not resolve the gate (R2)."""
    bot = _FakeBot(
        [],
        [
            _msg(1, "approve", update_id=1, chat_id=999),  # other chat
            _msg(1, "reject", update_id=2, chat_id=_OPERATOR_CHAT),  # operator chat
        ],
        allowed_users={1},
    )
    assert _approver(bot).request_approval(_req()) is ApprovalDecision.REJECT


def test_a_reply_from_a_non_allowlisted_user_is_ignored() -> None:
    """A non-allowlisted user's reply is never a decision; only the allowlisted one counts."""
    bot = _FakeBot(
        [],
        [_msg(2, "approve", update_id=1), _msg(1, "approve", update_id=2)],
        allowed_users={1},
    )
    assert _approver(bot).request_approval(_req()) is ApprovalDecision.APPROVE


def test_an_ambiguous_token_is_not_a_decision() -> None:
    """Only the documented APPROVE/REJECT count; 'yes'/chatter are ignored (R3)."""
    bot = _FakeBot(
        [],
        [_msg(1, "yes", update_id=1), _msg(1, "reject", update_id=2)],
        allowed_users={1},
    )
    # 'yes' is not the documented command, so it is ignored; the explicit reject resolves the gate
    assert _approver(bot).request_approval(_req()) is ApprovalDecision.REJECT
