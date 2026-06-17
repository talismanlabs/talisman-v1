"""Tests for enforcing accepted cross-family review before slice closure."""

import pytest

from talisman_core.domain import ReviewRecommendation, ReviewResult, ReviewStatus
from talisman_core.policies import (
    SliceClosureError,
    agent_family,
    ensure_slice_may_close,
    evaluate_slice_closure,
)


def _review(
    *,
    lead_agent: str = "claude_code",
    review_agent: str = "codex_cli",
    status: ReviewStatus = ReviewStatus.PASS,
    recommendation: ReviewRecommendation = ReviewRecommendation.ACCEPT,
) -> ReviewResult:
    """Build a review result for policy tests."""
    return ReviewResult(
        slice_id="S08.02",
        lead_agent=lead_agent,
        review_agent=review_agent,
        status=status,
        recommendation=recommendation,
    )


def test_agent_family_maps_known_agents_and_falls_back_to_agent_name() -> None:
    """Known agents resolve to vendor families while unknown agents remain distinct."""
    assert agent_family("claude_code") == "anthropic"
    assert agent_family("codex_cli") == "openai"
    assert agent_family("local_reviewer") == "local_reviewer"


def test_no_review_artifact_prevents_closure_and_raises() -> None:
    """A slice cannot close when no review artifact has been saved."""
    decision = evaluate_slice_closure(None)

    assert decision.allowed is False
    assert "no review artifact" in decision.reason
    with pytest.raises(SliceClosureError, match="no review artifact"):
        ensure_slice_may_close(None)


def test_same_family_review_prevents_closure_and_raises() -> None:
    """A same-family review cannot satisfy the cross-family review requirement."""
    review = _review(lead_agent="claude_code", review_agent="claude")

    decision = evaluate_slice_closure(review)

    assert decision.allowed is False
    assert "cross-family" in decision.reason
    with pytest.raises(SliceClosureError, match="cross-family"):
        ensure_slice_may_close(review)


@pytest.mark.parametrize(
    "recommendation",
    [ReviewRecommendation.REVISE, ReviewRecommendation.REJECT],
)
def test_cross_family_non_accept_recommendation_prevents_closure(
    recommendation: ReviewRecommendation,
) -> None:
    """A cross-family review must still recommend acceptance to permit closure."""
    review = _review(recommendation=recommendation)

    decision = evaluate_slice_closure(review)

    assert decision.allowed is False
    assert "recommendation" in decision.reason
    assert recommendation.value in decision.reason
    with pytest.raises(SliceClosureError, match="recommendation"):
        ensure_slice_may_close(review)


def test_cross_family_block_status_prevents_closure() -> None:
    """A blocking status prevents closure even with an accept recommendation."""
    review = _review(status=ReviewStatus.BLOCK)

    decision = evaluate_slice_closure(review)

    assert decision.allowed is False
    assert "block" in decision.reason
    with pytest.raises(SliceClosureError, match="block"):
        ensure_slice_may_close(review)


@pytest.mark.parametrize("status", [ReviewStatus.PASS, ReviewStatus.PASS_WITH_NOTES])
def test_cross_family_accepting_non_block_review_permits_closure(status: ReviewStatus) -> None:
    """A cross-family accept review with non-block status permits slice closure."""
    review = _review(status=status)

    decision = evaluate_slice_closure(review)

    assert decision.allowed is True
    assert "permits closure" in decision.reason
    ensure_slice_may_close(review)
