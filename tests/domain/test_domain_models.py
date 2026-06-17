"""Tests for the pure domain models (slice S02.01)."""

import dataclasses
from pathlib import Path

import pytest

from talisman_core.domain import (
    Artifact,
    Gate,
    GateStatus,
    Project,
    ReviewRecommendation,
    ReviewResult,
    ReviewStatus,
    WorkflowTier,
)


def test_project_carries_tier_and_path() -> None:
    """A Project holds its tier as an enum and its root as a Path."""
    project = Project(
        project_id="p1",
        title="Demo",
        tier=WorkflowTier.FULL_SPIRAL,
        root_path=Path("/tmp/p1"),
    )
    assert project.tier is WorkflowTier.FULL_SPIRAL
    assert project.tier.value == "full_spiral"
    assert project.root_path.name == "p1"


def test_gate_records_decision_state() -> None:
    """A Gate names the project, the gate, and its current decision status."""
    gate = Gate(gate_id="g1", project_id="p1", name="interview", status=GateStatus.PENDING)
    assert gate.status is GateStatus.PENDING
    assert {s.value for s in GateStatus} >= {"pending", "approved", "rejected"}


def test_artifact_points_at_an_output() -> None:
    """An Artifact references a produced output by kind and path."""
    artifact = Artifact(
        artifact_id="a1",
        project_id="p1",
        kind="plan",
        path=Path("/tmp/plan.md"),
        summary="initial plan",
    )
    assert artifact.kind == "plan"
    assert artifact.path.name == "plan.md"


def test_review_result_models_cross_family_outcome() -> None:
    """A ReviewResult records lead/reviewer agents and the verdict."""
    result = ReviewResult(
        slice_id="S02.01",
        lead_agent="claude_code",
        review_agent="codex_cli",
        status=ReviewStatus.PASS,
        recommendation=ReviewRecommendation.ACCEPT,
    )
    assert result.lead_agent != result.review_agent
    assert result.recommendation is ReviewRecommendation.ACCEPT


def test_domain_models_are_immutable() -> None:
    """Frozen dataclasses reject attribute mutation, protecting invariants."""
    project = Project(
        project_id="p1",
        title="Demo",
        tier=WorkflowTier.LIGHTWEIGHT,
        root_path=Path("."),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        project.title = "changed"  # type: ignore[misc]
