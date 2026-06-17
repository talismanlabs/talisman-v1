"""SQLite-backed budget ledger and pre-call circuit breaker.

The budget ledger is infrastructure-local for this slice: gateway-side code can
record spend durably and check projected daily/monthly hard caps before any
provider request without adding a new core port.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import cast

from talisman_core.adapters.sqlite.migrations import initialize_database

_INSERT_BUDGET_EVENT_SQL = """
INSERT INTO budget_events (project_id, cost_usd)
VALUES (?, ?)
"""
_SELECT_BUDGET_EVENT_BY_ID_SQL = """
SELECT id, project_id, cost_usd, created_at
FROM budget_events
WHERE id = ?
"""
_SUM_BUDGET_EVENTS_SINCE_SQL = """
SELECT COALESCE(SUM(cost_usd), 0.0)
FROM budget_events
WHERE created_at >= ?
"""
_BudgetEventRow = tuple[int, str | None, float, str]


class BudgetDecision(str, Enum):
    """Pre-call budget circuit-breaker decision."""

    ALLOWED = "allowed"
    PAUSE_DAILY = "pause_daily"
    PAUSE_MONTHLY = "pause_monthly"


class BudgetCircuitOpen(RuntimeError):
    """Raised when a projected provider request would breach a hard cap."""

    def __init__(self, decision: BudgetDecision) -> None:
        """Initialize the exception with the failing budget decision."""
        super().__init__(f"Budget circuit breaker paused call: {decision.value}")
        self.decision: BudgetDecision = decision


@dataclass(frozen=True, slots=True)
class BudgetEvent:
    """A persisted budget spend event row."""

    id: int
    project_id: str | None
    cost_usd: float
    created_at: str


class SQLiteBudgetAdapter:
    """Record spend and evaluate hard-cap budget breakers in SQLite."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the budget adapter and ensure the schema exists."""
        self._db_path = db_path
        initialize_database(db_path)

    def record_spend(self, cost_usd: float, project_id: str | None = None) -> BudgetEvent:
        """Persist one spend event and return its stored row."""
        _validate_non_negative("cost_usd", cost_usd)
        connection = sqlite3.connect(self._db_path)
        try:
            cursor = connection.execute(
                _INSERT_BUDGET_EVENT_SQL,
                (project_id, cost_usd),
            )
            event_id = cursor.lastrowid
            if event_id is None:
                raise RuntimeError("SQLite did not report a budget event id after insert.")

            row = connection.execute(
                _SELECT_BUDGET_EVENT_BY_ID_SQL,
                (event_id,),
            ).fetchone()
            connection.commit()
        finally:
            connection.close()

        if row is None:
            raise RuntimeError(f"Inserted budget event {event_id} could not be reloaded.")
        return _budget_event_from_row(row)

    def current_daily_spend_usd(self) -> float:
        """Return total recorded spend since the current UTC day began."""
        return self._sum_cost_since(_start_of_today_utc())

    def current_monthly_spend_usd(self) -> float:
        """Return total recorded spend since the current UTC month began."""
        return self._sum_cost_since(_start_of_month_utc())

    def check_call(
        self,
        *,
        estimated_cost_usd: float,
        daily_hard_usd: float,
        monthly_hard_usd: float,
    ) -> BudgetDecision:
        """Return whether a projected provider call may proceed.

        The check is read-only and intended to run before the provider request.
        A projected total equal to the hard cap is allowed; a projected total
        above the hard cap pauses work. If both caps would be breached, the
        daily pause is reported first because it is the narrower circuit.
        """
        _validate_non_negative("estimated_cost_usd", estimated_cost_usd)
        _validate_non_negative("daily_hard_usd", daily_hard_usd)
        _validate_non_negative("monthly_hard_usd", monthly_hard_usd)

        if self.current_daily_spend_usd() + estimated_cost_usd > daily_hard_usd:
            return BudgetDecision.PAUSE_DAILY
        if self.current_monthly_spend_usd() + estimated_cost_usd > monthly_hard_usd:
            return BudgetDecision.PAUSE_MONTHLY
        return BudgetDecision.ALLOWED

    def require_call_allowed(
        self,
        *,
        estimated_cost_usd: float,
        daily_hard_usd: float,
        monthly_hard_usd: float,
    ) -> None:
        """Raise ``BudgetCircuitOpen`` unless a projected call is allowed."""
        decision = self.check_call(
            estimated_cost_usd=estimated_cost_usd,
            daily_hard_usd=daily_hard_usd,
            monthly_hard_usd=monthly_hard_usd,
        )
        if decision is not BudgetDecision.ALLOWED:
            raise BudgetCircuitOpen(decision)

    def _sum_cost_since(self, cutoff_utc: str) -> float:
        connection = sqlite3.connect(self._db_path)
        try:
            row = connection.execute(
                _SUM_BUDGET_EVENTS_SINCE_SQL,
                (cutoff_utc,),
            ).fetchone()
        finally:
            connection.close()

        if row is None:
            raise RuntimeError("SQLite did not return a budget total.")
        return float(row[0])


def _budget_event_from_row(row: object) -> BudgetEvent:
    event_id, project_id, cost_usd, created_at = cast(_BudgetEventRow, row)
    return BudgetEvent(
        id=event_id,
        project_id=project_id,
        cost_usd=cost_usd,
        created_at=created_at,
    )


def _start_of_today_utc() -> str:
    now = datetime.now(UTC)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return _format_sqlite_timestamp(start)


def _start_of_month_utc() -> str:
    now = datetime.now(UTC)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return _format_sqlite_timestamp(start)


def _format_sqlite_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _validate_non_negative(name: str, value: float) -> None:
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative.")
