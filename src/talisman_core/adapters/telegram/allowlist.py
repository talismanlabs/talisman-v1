"""Telegram user allowlist enforcement (slice S05.01).

The Telegram control plane must reject any command from a user who is not on the
allowlist before processing it (architecture decision D3 hardening). The allowlist
is a set of numeric Telegram user IDs loaded from an operator-supplied secret file
at startup; the file itself is never committed (see ``.gitignore``). This module
holds only the membership logic, so it is testable without a live bot or any secret.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TelegramAllowlist:
    """An immutable set of Telegram user IDs permitted to command TalisMan."""

    allowed_user_ids: frozenset[int]

    def is_allowed(self, user_id: int) -> bool:
        """Return True only if the user id is on the allowlist."""
        return user_id in self.allowed_user_ids

    def ensure_allowed(self, user_id: int) -> None:
        """Raise ``PermissionError`` if the user id is not on the allowlist.

        This is the explicit rejection used by the command handler before any
        approval action is applied.
        """
        if not self.is_allowed(user_id):
            raise PermissionError(f"Telegram user {user_id} is not allowlisted.")


def load_allowlist(path: Path) -> TelegramAllowlist:
    """Load an allowlist from a secret file of one numeric user id per line.

    Blank lines and lines beginning with ``#`` are ignored. The file lives outside
    the repository and is supplied by the operator; this loader reads ids only,
    never secrets embedded in code.
    """
    user_ids: set[int] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        user_ids.add(int(line))
    return TelegramAllowlist(frozenset(user_ids))
