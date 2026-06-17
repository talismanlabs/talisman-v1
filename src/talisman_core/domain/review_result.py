"""The ReviewResult domain model.

Captures the outcome of an inter-agent review of an implementation slice. This is
the domain-level mirror of the YAML review artifact recorded under ``docs/reviews/``:
it names the lead and reviewing agents and records the review status and final
recommendation. Cross-family review (opposite-family reviewer) is mandatory, but
that routing rule is a policy concern, not a domain one.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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


@dataclass(frozen=True)
class ReviewResult:
    """Immutable record of one inter-agent review outcome."""

    slice_id: str
    lead_agent: str
    review_agent: str
    status: ReviewStatus
    recommendation: ReviewRecommendation
