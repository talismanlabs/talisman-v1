"""Tests for the portfolio scheduler."""

from datetime import UTC, datetime, timedelta

import pytest

from talisman_core.scheduler.portfolio import PortfolioScheduler, ScheduledTask


class _ManualClock:
    """Deterministic clock for scheduler tests."""

    def __init__(self, current: datetime) -> None:
        self.current = current

    def __call__(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


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


def test_duplicate_task_id_is_rejected() -> None:
    """A task id already queued or active cannot be enqueued again (cap-safety)."""
    scheduler = PortfolioScheduler(active_slot_limit=2)
    scheduler.enqueue(ScheduledTask("dup", "p"))
    with pytest.raises(ValueError, match="already scheduled"):
        scheduler.enqueue(ScheduledTask("dup", "p"))


def test_duplicate_ids_cannot_bypass_the_cap() -> None:
    """Uniqueness enforcement prevents two tasks from sharing one active slot."""
    scheduler = PortfolioScheduler(active_slot_limit=2)
    scheduler.enqueue(ScheduledTask("a", "p"))
    with pytest.raises(ValueError):
        scheduler.enqueue(ScheduledTask("a", "p"))
    scheduler.start_next()
    assert scheduler.active_count == 1  # accurate count, not collapsed


def test_task_id_reusable_after_completion() -> None:
    """An id may be reused once its task has completed and freed its slot."""
    scheduler = PortfolioScheduler(active_slot_limit=1)
    scheduler.enqueue(ScheduledTask("a", "p"))
    scheduler.start_next()
    scheduler.complete("a")
    scheduler.enqueue(ScheduledTask("a", "p"))  # allowed now
    assert scheduler.queued_count == 1


def test_wait_time_is_tracked_per_project() -> None:
    """Project wait metrics include queued waits and waits recorded at start time."""
    start = datetime(2026, 1, 1, tzinfo=UTC)
    clock = _ManualClock(start)
    scheduler = PortfolioScheduler(active_slot_limit=1, clock=clock)

    scheduler.enqueue(ScheduledTask("p1-task", "p1"))
    clock.advance(timedelta(minutes=10))
    scheduler.enqueue(ScheduledTask("p2-task", "p2"))
    clock.advance(timedelta(minutes=5))

    queued_metrics = scheduler.wait_metrics_by_project()
    assert queued_metrics["p1"].queued_count == 1
    assert queued_metrics["p1"].started_count == 0
    assert queued_metrics["p1"].total_wait_seconds == 900.0
    assert queued_metrics["p1"].longest_wait_seconds == 900.0
    assert queued_metrics["p2"].total_wait_seconds == 300.0

    started = scheduler.start_next()

    assert started is not None
    assert started.enqueued_at == start
    assert started.started_at == start + timedelta(minutes=15)
    assert started.total_wait_seconds == 900.0
    started_metrics = scheduler.wait_metrics_by_project()
    assert started_metrics["p1"].queued_count == 0
    assert started_metrics["p1"].started_count == 1
    assert started_metrics["p1"].total_wait_seconds == 900.0


def test_aging_promotes_task_past_threshold_one_priority_level() -> None:
    """A queued task waiting past the threshold is promoted once."""
    clock = _ManualClock(datetime(2026, 1, 1, tzinfo=UTC))
    scheduler = PortfolioScheduler(active_slot_limit=1, clock=clock)
    scheduler.enqueue(ScheduledTask("old", "p", priority=0))
    clock.advance(timedelta(hours=25))
    scheduler.enqueue(ScheduledTask("newer", "p", priority=1))

    assert scheduler.apply_aging() == 1
    started = scheduler.start_next()

    assert started is not None
    assert started.task_id == "old"
    assert started.priority == 1


def test_aging_does_not_promote_task_under_threshold() -> None:
    """A queued task under the aging threshold keeps its original priority."""
    clock = _ManualClock(datetime(2026, 1, 1, tzinfo=UTC))
    scheduler = PortfolioScheduler(active_slot_limit=1, clock=clock)
    scheduler.enqueue(ScheduledTask("young", "p", priority=0))
    clock.advance(timedelta(hours=23, minutes=59))
    scheduler.enqueue(ScheduledTask("newer", "p", priority=1))

    assert scheduler.apply_aging() == 0
    started = scheduler.start_next()

    assert started is not None
    assert started.task_id == "newer"
    assert started.priority == 1


def test_aging_does_not_promote_task_blocked_on_user_approval() -> None:
    """A queued task blocked on user approval is skipped by aging."""
    clock = _ManualClock(datetime(2026, 1, 1, tzinfo=UTC))
    scheduler = PortfolioScheduler(active_slot_limit=1, clock=clock)
    scheduler.enqueue(ScheduledTask("blocked", "p", priority=0))
    scheduler.mark_blocked_on_user_approval("blocked")
    clock.advance(timedelta(hours=25))
    scheduler.enqueue(ScheduledTask("newer", "p", priority=1))

    assert scheduler.apply_aging() == 0
    started = scheduler.start_next()

    assert started is not None
    assert started.task_id == "newer"
    assert started.priority == 1


def test_aging_does_not_repeat_within_same_wait_window() -> None:
    """Successive aging calls in one threshold window do not repeatedly promote."""
    clock = _ManualClock(datetime(2026, 1, 1, tzinfo=UTC))
    scheduler = PortfolioScheduler(active_slot_limit=1, clock=clock)
    scheduler.enqueue(ScheduledTask("old", "p", priority=0))
    clock.advance(timedelta(hours=25))

    assert scheduler.apply_aging() == 1
    assert scheduler.apply_aging() == 0
    clock.advance(timedelta(hours=1))
    assert scheduler.apply_aging() == 0
    started = scheduler.start_next()

    assert started is not None
    assert started.priority == 1
