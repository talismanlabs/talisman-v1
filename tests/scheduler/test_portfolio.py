"""Tests for the portfolio scheduler's active-slot cap (slice S11.01)."""

import pytest

from talisman_core.scheduler.portfolio import PortfolioScheduler, ScheduledTask


def test_active_slot_cap_is_enforced() -> None:
    """No more than `active_slot_limit` tasks can be active at once."""
    scheduler = PortfolioScheduler(active_slot_limit=2)
    for i in range(4):
        scheduler.enqueue(ScheduledTask(task_id=f"t{i}", project_id="p"))

    started = [scheduler.start_next() for _ in range(4)]

    assert started[0] is not None
    assert started[1] is not None
    assert started[2] is None  # cap reached
    assert started[3] is None
    assert scheduler.active_count == 2
    assert scheduler.queued_count == 2


def test_completing_a_task_frees_a_slot() -> None:
    """Completing an active task lets the next queued task start."""
    scheduler = PortfolioScheduler(active_slot_limit=1)
    scheduler.enqueue(ScheduledTask("a", "p"))
    scheduler.enqueue(ScheduledTask("b", "p"))

    first = scheduler.start_next()
    assert first is not None and first.task_id == "a"
    assert scheduler.start_next() is None  # at capacity

    scheduler.complete("a")
    second = scheduler.start_next()
    assert second is not None and second.task_id == "b"


def test_priority_then_fifo_selection() -> None:
    """Higher priority starts first; equal priority is served in enqueue order."""
    scheduler = PortfolioScheduler(active_slot_limit=1)
    scheduler.enqueue(ScheduledTask("low1", "p", priority=0))
    scheduler.enqueue(ScheduledTask("high", "p", priority=5))
    scheduler.enqueue(ScheduledTask("low2", "p", priority=0))

    high = scheduler.start_next()
    assert high is not None and high.task_id == "high"
    scheduler.complete("high")
    low1 = scheduler.start_next()
    assert low1 is not None and low1.task_id == "low1"


def test_invalid_slot_limit_is_rejected() -> None:
    """A scheduler must have at least one slot."""
    with pytest.raises(ValueError, match="at least 1"):
        PortfolioScheduler(active_slot_limit=0)
