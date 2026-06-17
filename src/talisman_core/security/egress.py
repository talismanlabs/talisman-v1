"""Pure egress allowlist policy (slice S10.02).

The security layer defaults to deny for outbound network destinations. A host is
allowed only when it exactly matches a configured allowlist entry or is a true
subdomain of one, using a dot boundary to avoid suffix-match bypasses.
"""

from __future__ import annotations

from collections.abc import Iterable

DEFAULT_EGRESS_ALLOWLIST: tuple[str, ...] = (
    "api.anthropic.com",
    "api.openai.com",
    "api.telegram.org",
    "github.com",
    "objects.githubusercontent.com",
    "raw.githubusercontent.com",
    "pypi.org",
    "files.pythonhosted.org",
    "deb.debian.org",
    "archive.ubuntu.com",
    "security.ubuntu.com",
)


class EgressDenied(RuntimeError):
    """Raised when a host is not permitted by the egress allowlist."""


def is_allowed(host: str, allowlist: Iterable[str] = DEFAULT_EGRESS_ALLOWLIST) -> bool:
    """Return whether ``host`` is permitted by the egress allowlist.

    Matching is case-insensitive after removing one trailing DNS root dot. A
    host is allowed only by exact match or by being a true subdomain separated
    by a dot boundary.
    """
    normalized_host = _normalize_host(host)
    if not normalized_host:
        return False

    for entry in allowlist:
        normalized_entry = _normalize_host(entry)
        if not normalized_entry:
            continue
        if normalized_host == normalized_entry:
            return True
        if normalized_host.endswith(f".{normalized_entry}"):
            return True
    return False


def ensure_allowed(host: str, allowlist: Iterable[str] = DEFAULT_EGRESS_ALLOWLIST) -> None:
    """Raise ``EgressDenied`` unless ``host`` is permitted by the allowlist."""
    if not is_allowed(host, allowlist):
        raise EgressDenied(f"Egress denied for host: {host}")


def _normalize_host(host: str) -> str:
    normalized = host.lower()
    if normalized.endswith("."):
        return normalized[:-1]
    return normalized
