"""Tests for the egress allowlist policy (slice S10.02)."""

import pytest

from talisman_core.security.egress import EgressDenied, ensure_allowed, is_allowed


def test_exact_allowlisted_hosts_are_allowed() -> None:
    """Exact hosts from the default allowlist are permitted."""
    assert is_allowed("api.anthropic.com")
    assert is_allowed("github.com")


def test_true_subdomain_of_allowlisted_entry_is_allowed() -> None:
    """Subdomains are allowed only below an allowlisted entry."""
    assert is_allowed("api.github.com")


def test_case_and_single_trailing_dot_are_normalized() -> None:
    """Host matching ignores case and one trailing DNS root dot."""
    assert is_allowed("API.ANTHROPIC.COM.")


def test_disallowed_hosts_are_denied_and_raise() -> None:
    """Hosts outside the allowlist fail closed."""
    assert not is_allowed("evil.com")
    assert not is_allowed("malware.test")
    with pytest.raises(EgressDenied, match="Egress denied for host: evil\\.com"):
        ensure_allowed("evil.com")


def test_suffix_not_subdomain_bypass_is_denied() -> None:
    """A bare suffix match must not allow lookalike domains."""
    assert not is_allowed("evilanthropic.com", allowlist=("anthropic.com",))


def test_allowlisted_string_in_middle_bypass_is_denied() -> None:
    """An allowlisted host embedded inside another domain is denied."""
    assert not is_allowed("api.anthropic.com.evil.com")
