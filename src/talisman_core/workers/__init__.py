"""Subprocess worker adapters wrapping Claude Code and Codex CLI.

Workers implement worker ports and may contain vendor-specific subprocess logic.
They execute under orchestrator direction and must not own policy or mutate global
project state directly.
"""
