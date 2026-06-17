"""The ReviewResult domain model.

Captures the outcome of an inter-agent review of an implementation slice. This is
the domain-level mirror of the YAML review artifact recorded under ``docs/reviews/``:
it names the lead and reviewing agents and records the review status and final
recommendation. Cross-family review (opposite-family reviewer) is mandatory, but
that routing rule is a policy concern, not a domain one.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ReviewStatus(str, Enum):
    """Top-level verdict a reviewer assigns to a slice."""

    PASS = "pass"
    PASS_WITH_NOTES = "pass_with_notes"
    BLOCK = "block"


class ReviewRecommendation(str, Enum):
    """The reviewer's recommended disposition for the slice."""

    ACCEPT = "accept"
    REVISE = "revise"
    REJECT = "reject"


class FindingSeverity(str, Enum):
    """Severity assigned to an individual review finding."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKER = "blocker"


@dataclass(frozen=True)
class Finding:
    """A single issue raised during review, with the fix it requires."""

    id: str
    severity: FindingSeverity
    finding: str
    required_fix: str


@dataclass(frozen=True)
class ReviewResult:
    """Immutable record of one inter-agent review outcome and its findings."""

    slice_id: str
    lead_agent: str
    review_agent: str
    status: ReviewStatus
    recommendation: ReviewRecommendation
    findings: tuple[Finding, ...] = ()


def review_to_dict(review: ReviewResult) -> dict[str, Any]:
    """Convert a ReviewResult to a plain, serializable dict.

    Pure data transformation — the domain performs no input/output. An adapter is
    responsible for writing the resulting dict to a review artifact file.
    """
    return {
        "slice_id": review.slice_id,
        "lead_agent": review.lead_agent,
        "review_agent": review.review_agent,
        "status": review.status.value,
        "recommendation": review.recommendation.value,
        "findings": [
            {
                "id": finding.id,
                "severity": finding.severity.value,
                "finding": finding.finding,
                "required_fix": finding.required_fix,
            }
            for finding in review.findings
        ],
    }


def review_from_dict(data: Mapping[str, Any]) -> ReviewResult:
    """Build a ReviewResult from a plain mapping (the inverse of ``review_to_dict``)."""
    findings = tuple(
        Finding(
            id=str(item["id"]),
            severity=FindingSeverity(item["severity"]),
            finding=str(item["finding"]),
            required_fix=str(item["required_fix"]),
        )
        for item in data.get("findings", ())
    )
    return ReviewResult(
        slice_id=str(data["slice_id"]),
        lead_agent=str(data["lead_agent"]),
        review_agent=str(data["review_agent"]),
        status=ReviewStatus(data["status"]),
        recommendation=ReviewRecommendation(data["recommendation"]),
        findings=findings,
    )
