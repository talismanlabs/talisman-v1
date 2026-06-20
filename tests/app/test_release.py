"""Tests for the v1 acceptance results (slice S15.01 → S15.02 formal acceptance)."""

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
    """Only fully-proven ATs are PASS — locks the honest grading after the Codex S15.01 review.

    v1 was accepted (2026-06-19) on five PASS criteria; live-demonstrated items keep
    COMPONENT_VERIFIED until their runtime code merges under governance (v1.1-P1). AT-13 is the
    first to harden to PASS: S16.03 wired the credential scrub into the worker subprocess runner,
    proven by a real-child CI test (tests/workers/test_subprocess_runner.py).
    """
    passing = {r.test_id for r in ACCEPTANCE_RESULTS if r.status is AcceptanceStatus.PASS}
    assert passing == {"AT-01", "AT-02", "AT-03", "AT-09", "AT-13", "AT-20"}


def test_v1_accepted_with_five_approved_waivers() -> None:
    """S15.02 acceptance: exactly five waivers remain, each carrying the founder's approval."""
    waived = [r for r in ACCEPTANCE_RESULTS if r.status is AcceptanceStatus.WAIVED]
    assert {r.test_id for r in waived} == {"AT-04", "AT-12", "AT-16", "AT-17", "AT-19"}
    for result in waived:
        assert result.waiver is not None
        assert "APPROVED" in result.waiver.approval


def test_live_demonstrated_items_are_not_waived() -> None:
    """AT-05 (Telegram) and AT-14 (egress) were demonstrated live, so they are not waived."""
    for test_id in ("AT-05", "AT-14"):
        result = next(r for r in ACCEPTANCE_RESULTS if r.test_id == test_id)
        assert result.status is AcceptanceStatus.COMPONENT_VERIFIED
        assert result.waiver is None


def test_checklist_renders_all_tests_and_a_summary() -> None:
    """The rendered checklist lists every test id and a summary line."""
    markdown = render_acceptance_checklist()
    assert "TalisMan v1 acceptance checklist" in markdown
    assert "**Summary:**" in markdown
    for result in ACCEPTANCE_RESULTS:
        assert result.test_id in markdown
