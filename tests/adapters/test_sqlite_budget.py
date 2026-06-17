"""Tests for SQLite budget spend persistence and circuit breakers."""

from pathlib import Path

import pytest

from talisman_core.adapters.sqlite.budget import (
    BudgetCircuitOpen,
    BudgetDecision,
    SQLiteBudgetAdapter,
)


def test_budget_check_under_hard_caps_allows_call(tmp_path: Path) -> None:
    """A projected call under both hard caps may proceed."""
    budget = SQLiteBudgetAdapter(tmp_path / "state" / "TalisMan.sqlite3")

    decision = budget.check_call(
        estimated_cost_usd=1.25,
        daily_hard_usd=10.0,
        monthly_hard_usd=60.0,
    )

    assert decision is BudgetDecision.ALLOWED


def test_daily_hard_cap_breach_pauses_before_call(tmp_path: Path) -> None:
    """Projected daily spend above the hard cap trips the daily breaker."""
    budget = SQLiteBudgetAdapter(tmp_path / "state" / "TalisMan.sqlite3")
    budget.record_spend(9.75, project_id="project-a")

    decision = budget.check_call(
        estimated_cost_usd=0.26,
        daily_hard_usd=10.0,
        monthly_hard_usd=60.0,
    )

    assert decision is BudgetDecision.PAUSE_DAILY
    with pytest.raises(BudgetCircuitOpen) as error:
        budget.require_call_allowed(
            estimated_cost_usd=0.26,
            daily_hard_usd=10.0,
            monthly_hard_usd=60.0,
        )
    assert error.value.decision is BudgetDecision.PAUSE_DAILY


def test_monthly_hard_cap_breach_pauses_before_call(tmp_path: Path) -> None:
    """Projected monthly spend above the hard cap trips the monthly breaker."""
    budget = SQLiteBudgetAdapter(tmp_path / "state" / "TalisMan.sqlite3")
    budget.record_spend(59.50, project_id="project-a")

    decision = budget.check_call(
        estimated_cost_usd=0.51,
        daily_hard_usd=100.0,
        monthly_hard_usd=60.0,
    )

    assert decision is BudgetDecision.PAUSE_MONTHLY
    with pytest.raises(BudgetCircuitOpen) as error:
        budget.require_call_allowed(
            estimated_cost_usd=0.51,
            daily_hard_usd=100.0,
            monthly_hard_usd=60.0,
        )
    assert error.value.decision is BudgetDecision.PAUSE_MONTHLY


def test_spend_persists_across_connections(tmp_path: Path) -> None:
    """A fresh adapter instance sees spend recorded by an earlier instance."""
    db_path = tmp_path / "state" / "TalisMan.sqlite3"
    writer = SQLiteBudgetAdapter(db_path)
    stored = writer.record_spend(2.25, project_id="project-a")

    reader = SQLiteBudgetAdapter(db_path)

    assert stored.id > 0
    assert stored.project_id == "project-a"
    assert stored.created_at
    assert reader.current_daily_spend_usd() == pytest.approx(2.25)
    assert reader.current_monthly_spend_usd() == pytest.approx(2.25)
