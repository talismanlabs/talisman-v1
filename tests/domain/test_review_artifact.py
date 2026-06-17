"""Tests for the structured review artifact format (slice S08.01)."""

from talisman_core.domain import (
    Finding,
    FindingSeverity,
    ReviewRecommendation,
    ReviewResult,
    ReviewStatus,
)
from talisman_core.domain.review_result import review_from_dict, review_to_dict


def _review_with_findings() -> ReviewResult:
    return ReviewResult(
        slice_id="S08.01",
        lead_agent="claude_code",
        review_agent="codex_cli",
        status=ReviewStatus.PASS_WITH_NOTES,
        recommendation=ReviewRecommendation.ACCEPT,
        findings=(
            Finding(
                id="R1", severity=FindingSeverity.MEDIUM, finding="an issue", required_fix="fix it"
            ),
            Finding(
                id="R2",
                severity=FindingSeverity.BLOCKER,
                finding="a blocker",
                required_fix="must fix",
            ),
        ),
    )


def test_review_result_carries_status_findings_and_required_fixes() -> None:
    """A review records its status plus structured findings with required fixes."""
    review = _review_with_findings()
    assert review.status is ReviewStatus.PASS_WITH_NOTES
    assert review.findings[1].severity is FindingSeverity.BLOCKER
    assert review.findings[0].required_fix == "fix it"


def test_review_round_trips_through_dict() -> None:
    """to_dict/from_dict preserve status, findings, and required fixes exactly."""
    review = _review_with_findings()
    data = review_to_dict(review)
    assert data["status"] == "pass_with_notes"
    assert data["findings"][1]["severity"] == "blocker"
    assert data["findings"][0]["required_fix"] == "fix it"
    assert review_from_dict(data) == review


def test_review_without_findings_defaults_to_empty() -> None:
    """Findings default to an empty tuple, keeping older reviews valid."""
    review = ReviewResult(
        slice_id="S08.01",
        lead_agent="claude_code",
        review_agent="codex_cli",
        status=ReviewStatus.PASS,
        recommendation=ReviewRecommendation.ACCEPT,
    )
    assert review.findings == ()
    assert review_to_dict(review)["findings"] == []
