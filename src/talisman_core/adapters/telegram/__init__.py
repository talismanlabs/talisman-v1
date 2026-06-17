"""Telegram control-plane adapter.

Telegram is the v1 user-facing control plane and lives in the adapters layer. This
package holds Telegram-specific infrastructure — the user allowlist now; bot wiring
and the ``ApprovalPort`` implementation in later slices. Long-lived secrets (bot
token, allowlist file) are read from operator-supplied files at startup and are
never committed.
"""
