"""Pure policy enforcing review requirements before slice closure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from talisman_core.domain import ReviewRecommendation, ReviewResult, ReviewStatus

_KNOWN_AGENT_FAMILIES: Final[dict[str, str]] = {
    "anthropic": "anthropic",
    "claude": "anthropic",
    "claude_code": "anthropic",
    "claude-code": "anthropic",
    "claude code": "anthropic",
    "openai": "openai",
    "codex": "openai",
    "codex_cli": "openai",
    "codex-cli": "openai",
    "codex cli": "openai",
}


@dataclass(frozen=True)
class ClosureDecision:
    """Decision explaining whether a reviewed implementation slice may close."""

    allowed: bool
    reason: str


class SliceClosureError(RuntimeError):
    """Raised when a slice closure attempt violates review policy."""


def agent_family(agent_name: str) -> str:
    """Return the vendor family for a known agent, or the agent name for unknowns."""
    return _KNOWN_AGENT_FAMILIES.get(agent_name.strip().lower(), agent_name)


def evaluate_slice_closure(review: ReviewResult | None) -> ClosureDecision:
    """Evaluate whether a slice has the accepted cross-family review required to close."""
    if review is None:
        return ClosureDecision(allowed=False, reason="no review artifact saved")

    lead_family = agent_family(review.lead_agent)
    review_family = agent_family(review.review_agent)
    if lead_family == review_family:
        return ClosureDecision(
            allowed=False,
            reason=(
                "review must be cross-family: "
                f"{review.lead_agent!r} and {review.review_agent!r} are both {lead_family!r}"
            ),
        )

    if review.recommendation is not ReviewRecommendation.ACCEPT:
        return ClosureDecision(
            allowed=False,
            reason=(f"review recommendation must be accept: got {review.recommendation.value!r}"),
        )

    if review.status is ReviewStatus.BLOCK:
        return ClosureDecision(
            allowed=False,
            reason="review status must not be block",
        )

    return ClosureDecision(allowed=True, reason="accepted cross-family review permits closure")


def ensure_slice_may_close(review: ReviewResult | None) -> None:
    """Raise SliceClosureError unless the review policy permits slice closure."""
    decision = evaluate_slice_closure(review)
    if not decision.allowed:
        raise SliceClosureError(decision.reason)
