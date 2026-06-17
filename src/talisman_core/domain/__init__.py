"""Pure domain model: projects, gates, artifacts, review results, and invariants.

The domain layer is the innermost ring. It must not import adapters, workers,
security, memory, observability, or app wiring (enforced by Import Linter). Keeping
the domain pure makes the core concepts portable across interfaces and future
implementations.
"""

from talisman_core.domain.artifact import Artifact
from talisman_core.domain.gate import Gate, GateStatus
from talisman_core.domain.project import Project, WorkflowTier
from talisman_core.domain.review_result import (
    Finding,
    FindingSeverity,
    ReviewRecommendation,
    ReviewResult,
    ReviewStatus,
)

__all__ = [
    "Artifact",
    "Finding",
    "FindingSeverity",
    "Gate",
    "GateStatus",
    "Project",
    "ReviewRecommendation",
    "ReviewResult",
    "ReviewStatus",
    "WorkflowTier",
]
