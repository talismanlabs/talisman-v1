"""Tests for the Telegram user allowlist (slice S05.01)."""

from pathlib import Path

import pytest

from talisman_core.adapters.telegram.allowlist import TelegramAllowlist, load_allowlist


def test_allowlisted_user_is_accepted() -> None:
    """A user id on the allowlist passes both checks."""
    allowlist = TelegramAllowlist(frozenset({111, 222}))
    assert allowlist.is_allowed(111)
    allowlist.ensure_allowed(222)  # must not raise


def test_non_allowlisted_user_is_rejected() -> None:
    """A user id absent from the allowlist is rejected."""
    allowlist = TelegramAllowlist(frozenset({111}))
    assert not allowlist.is_allowed(999)
    with pytest.raises(PermissionError):
        allowlist.ensure_allowed(999)


def test_empty_allowlist_rejects_everyone() -> None:
    """An empty allowlist admits no one (fail-closed)."""
    allowlist = TelegramAllowlist(frozenset())
    assert not allowlist.is_allowed(1)


def test_load_allowlist_parses_ids_and_ignores_comments(tmp_path: Path) -> None:
    """The loader reads numeric ids, ignoring blank lines and comments."""
    path = tmp_path / "telegram_user_allowlist.secret"
    path.write_text("# allowed operators\n111\n\n222\n", encoding="utf-8")
    allowlist = load_allowlist(path)
    assert allowlist.is_allowed(111)
    assert allowlist.is_allowed(222)
    assert not allowlist.is_allowed(333)
