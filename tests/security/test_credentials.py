"""Tests for worker-environment credential scrubbing (slice S10.01)."""

from talisman_core.security.credentials import DEFAULT_SCRUBBED_VARS, scrub_environment


def test_scrub_removes_provider_keys_and_keeps_other_vars() -> None:
    """The provider/cloud secrets are stripped; ordinary variables are preserved."""
    base = {
        "ANTHROPIC_API_KEY": "dummy-anthropic",
        "OPENAI_API_KEY": "dummy-openai",
        "GITHUB_TOKEN": "dummy-gh",
        "PATH": "/usr/bin",
        "HOME": "/home/x",
    }
    scrubbed = scrub_environment(base)
    assert "ANTHROPIC_API_KEY" not in scrubbed
    assert "OPENAI_API_KEY" not in scrubbed
    assert "GITHUB_TOKEN" not in scrubbed
    assert scrubbed["PATH"] == "/usr/bin"
    assert scrubbed["HOME"] == "/home/x"


def test_default_scrub_list_covers_provider_and_cloud_keys() -> None:
    """The default scrub list includes the provider and cloud credentials."""
    assert {
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "GITHUB_TOKEN",
    } <= set(DEFAULT_SCRUBBED_VARS)


def test_scrub_accepts_custom_secret_names() -> None:
    """A caller may supply its own list of variables to strip."""
    base = {"FOO_TOKEN": "secret", "BAR": "ok"}
    scrubbed = scrub_environment(base, secret_names=["FOO_TOKEN"])
    assert "FOO_TOKEN" not in scrubbed
    assert scrubbed["BAR"] == "ok"
