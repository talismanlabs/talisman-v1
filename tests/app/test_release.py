"""Tests for the v1 acceptance results (slice S15.01)."""

from talisman_core.app.release import (
    ACCEPTANCE_RESULTS,
    AcceptanceStatus,
    render_acceptance_checklist,
    status_counts,
)


def test_every_acceptance_test_is_accounted_for() -> None:
    """AT-01..AT-20 are all present exactly once."""
    ids = [r.test_id for r in ACCEPTANCE_RESULTS]
    assert ids == [f"AT-{n:02d}" for n in range(1, 21)]
    assert len(set(ids)) == 20


def test_every_waived_test_has_a_complete_waiver() -> None:
    """The acceptance plan requires a reason, risk, compensating control, and approval."""
    for result in ACCEPTANCE_RESULTS:
        if result.status is AcceptanceStatus.WAIVED:
            waiver = result.waiver
            assert waiver is not None, f"{result.test_id} is waived without a waiver"
            assert waiver.reason
            assert waiver.risk
            assert waiver.compensating_control
            assert waiver.approval
        else:
            assert result.waiver is None, f"{result.test_id} is not waived but has a waiver"


def test_status_counts_cover_all_twenty() -> None:
    """Every result has a status and the counts sum to twenty."""
    counts = status_counts()
    assert sum(counts.values()) == 20
    assert counts[AcceptanceStatus.PASS] >= 1


def test_only_end_to_end_proven_criteria_are_pass() -> None:
    """Only fully-proven ATs are PASS — locks the honest grading after the Codex S15.01 review."""
    passing = {r.test_id for r in ACCEPTANCE_RESULTS if r.status is AcceptanceStatus.PASS}
    assert passing == {"AT-01", "AT-02", "AT-03", "AT-09", "AT-20"}


def test_checklist_renders_all_tests_and_a_summary() -> None:
    """The rendered checklist lists every test id and a summary line."""
    markdown = render_acceptance_checklist()
    assert "TalisMan v1 acceptance checklist" in markdown
    assert "**Summary:**" in markdown
    for result in ACCEPTANCE_RESULTS:
        assert result.test_id in markdown
