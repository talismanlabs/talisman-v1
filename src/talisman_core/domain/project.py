"""The Project domain model and workflow tier.

Ported from the canonical scaffold in
``docs/talisman-v1/talisman-v1-config-templates.md``. The domain model intentionally
contains no Telegram, SQLite, LangGraph, or worker-specific behavior, which keeps the
project concept portable across interfaces and future implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class WorkflowTier(str, Enum):
    """Supported workflow intensity levels.

    The tier controls review depth and gate count. The user may override the
    recommended tier because TalisMan is a human-governed assistant, not an
    autonomous authority.
    """

    LIGHTWEIGHT = "lightweight"
    FULL_SPIRAL = "full_spiral"


@dataclass(frozen=True)
class Project:
    """Immutable description of a TalisMan project."""

    project_id: str
    title: str
    tier: WorkflowTier
    root_path: Path
