"""Security layer: credential proxy, egress allowlist, retry/backoff, sandboxing.

Implements host-side credential isolation, egress allowlist enforcement, retry
policy with full jitter, and container/sandbox boundaries. No core module may store
or read long-lived secrets directly; workers receive scoped access via the proxy.
"""
