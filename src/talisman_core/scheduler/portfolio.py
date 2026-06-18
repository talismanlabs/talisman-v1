"""Portfolio scheduler with wait-time tracking and aging promotion.

Caps the number of concurrently active worker slots across all projects (default 3,
per architecture decision D8). Tasks are enqueued and started in priority-then-FIFO
order; the scheduler never lets more than the slot limit run at once. Queued task
wait time is tracked per project, and aging promotion raises long-waiting queued
tasks by one priority level per threshold crossing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta


DEFAULT_AGING_THRESHOLD = timedelta(hours=24)
_WAITING_FOR_SLOT = "waiting_for_slot"
_BLOCKED_ON_USER_APPROVAL = "blocked_on_user_approval"


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class ScheduledTask:
    """A unit of work waiting for, or holding, a worker slot."""

    task_id: str
    project_id: str
    priority: int = 0  # higher starts first; ties are broken FIFO (enqueue order)
    enqueued_at: datetime | None = None
    started_at: datetime | None = None
    total_wait_seconds: float = 0.0
    last_wait_reason: str | None = None
    blocked_on_user_approval: bool = False
    aging_promotions_applied: int = 0


@dataclass(frozen=True)
class ProjectWaitMetrics:
    """Aggregated wait-time metrics for a single project."""

    project_id: str
    queued_count: int
    started_count: int
    total_wait_seconds: float
    longest_wait_seconds: float
    last_wait_reason: str | None = None


@dataclass
class _WaitAccumulator:
    project_id: str
    queued_count: int = 0
    started_count: int = 0
    total_wait_seconds: float = 0.0
    longest_wait_seconds: float = 0.0
    last_wait_reason: str | None = None


class PortfolioScheduler:
    """Enforce the active worker-slot cap across queued tasks."""

    def __init__(
        self,
        active_slot_limit: int = 3,
        *,
        clock: Callable[[], datetime] = _utc_now,
        aging_threshold: timedelta = DEFAULT_AGING_THRESHOLD,
    ) -> None:
        """Create a scheduler with a slot cap, deterministic clock, and aging threshold."""
        if active_slot_limit < 1:
            raise ValueError("active_slot_limit must be at least 1.")
        if aging_threshold <= timedelta(0):
            raise ValueError("aging_threshold must be positive.")
        self._limit = active_slot_limit
        self._clock = clock
        self._aging_threshold = aging_threshold
        self._queued: list[ScheduledTask] = []
        self._active: dict[str, ScheduledTask] = {}
        self._started_wait_totals: dict[str, float] = {}
        self._started_wait_longest: dict[str, float] = {}
        self._started_wait_counts: dict[str, int] = {}
        self._last_wait_reasons: dict[str, str | None] = {}

    @property
    def active_count(self) -> int:
        """Number of tasks currently holding a worker slot."""
        return len(self._active)

    @property
    def queued_count(self) -> int:
        """Number of tasks waiting for a worker slot."""
        return len(self._queued)

    def has_free_slot(self) -> bool:
        """Whether a worker slot is available right now."""
        return self.active_count < self._limit

    def is_scheduled(self, task_id: str) -> bool:
        """Whether a task id is currently queued or active."""
        return task_id in self._active or any(t.task_id == task_id for t in self._queued)

    def enqueue(self, task: ScheduledTask) -> None:
        """Add a task to the wait queue.

        Task ids must be unique across queued and active tasks: a duplicate id would
        overwrite an active entry, undercount active slots, and silently bypass the
        cap, so it is rejected. An id may be reused once its task completes.
        """
        if self.is_scheduled(task.task_id):
            raise ValueError(f"task_id already scheduled: {task.task_id!r}")
        last_wait_reason = (
            _BLOCKED_ON_USER_APPROVAL if task.blocked_on_user_approval else _WAITING_FOR_SLOT
        )
        self._queued.append(
            replace(
                task,
                enqueued_at=self._clock(),
                started_at=None,
                total_wait_seconds=0.0,
                last_wait_reason=last_wait_reason,
                aging_promotions_applied=0,
            )
        )

    def start_next(self) -> ScheduledTask | None:
        """Start the next task if a slot is free.

        Returns the started task, or ``None`` when the active-slot cap is reached or
        the queue is empty. Selection is highest priority first, ties broken FIFO.
        """
        if not self.has_free_slot() or not self._queued:
            return None
        index = max(
            range(len(self._queued)),
            key=lambda i: (self._queued[i].priority, -i),
        )
        task = self._queued.pop(index)
        started_at = self._clock()
        started_task = replace(
            task,
            started_at=started_at,
            total_wait_seconds=self._wait_seconds(task, started_at),
        )
        self._active[task.task_id] = started_task
        self._record_started_wait(started_task)
        return started_task

    def complete(self, task_id: str) -> None:
        """Free the worker slot held by an active task (no-op if not active)."""
        self._active.pop(task_id, None)

    def mark_blocked_on_user_approval(self, task_id: str, blocked: bool = True) -> None:
        """Mark a scheduled task as blocked or unblocked on user approval."""
        last_wait_reason = _BLOCKED_ON_USER_APPROVAL if blocked else _WAITING_FOR_SLOT
        for index, task in enumerate(self._queued):
            if task.task_id == task_id:
                self._queued[index] = replace(
                    task,
                    blocked_on_user_approval=blocked,
                    last_wait_reason=last_wait_reason,
                )
                return
        if task_id in self._active:
            task = self._active[task_id]
            self._active[task_id] = replace(
                task,
                blocked_on_user_approval=blocked,
                last_wait_reason=last_wait_reason,
            )
            return
        raise ValueError(f"task_id is not scheduled: {task_id!r}")

    def apply_aging(
        self,
        *,
        now: datetime | None = None,
        blocked_task_ids: Iterable[str] = (),
    ) -> int:
        """Promote queued tasks once per aging-threshold crossing.

        Tasks marked or passed as blocked on user approval are skipped. The return
        value is the number of priority levels applied across all queued tasks.
        """
        effective_now = self._clock() if now is None else now
        blocked_ids = set(blocked_task_ids)
        promotions_applied = 0

        for index, task in enumerate(self._queued):
            if task.blocked_on_user_approval or task.task_id in blocked_ids:
                self._queued[index] = replace(task, last_wait_reason=_BLOCKED_ON_USER_APPROVAL)
                continue

            aging_windows = self._aging_windows(task, effective_now)
            promotions_due = aging_windows - task.aging_promotions_applied
            if promotions_due <= 0:
                if task.last_wait_reason != _WAITING_FOR_SLOT:
                    self._queued[index] = replace(task, last_wait_reason=_WAITING_FOR_SLOT)
                continue

            self._queued[index] = replace(
                task,
                priority=task.priority + promotions_due,
                last_wait_reason=_WAITING_FOR_SLOT,
                aging_promotions_applied=aging_windows,
            )
            promotions_applied += promotions_due

        return promotions_applied

    def wait_metrics_by_project(self, now: datetime | None = None) -> dict[str, ProjectWaitMetrics]:
        """Return current wait-time metrics keyed by project id."""
        effective_now = self._clock() if now is None else now
        accumulators: dict[str, _WaitAccumulator] = {}

        for project_id, total_wait_seconds in self._started_wait_totals.items():
            accumulator = self._accumulator_for(accumulators, project_id)
            accumulator.started_count = self._started_wait_counts[project_id]
            accumulator.total_wait_seconds += total_wait_seconds
            accumulator.longest_wait_seconds = max(
                accumulator.longest_wait_seconds,
                self._started_wait_longest[project_id],
            )
            accumulator.last_wait_reason = self._last_wait_reasons.get(project_id)

        for task in self._queued:
            accumulator = self._accumulator_for(accumulators, task.project_id)
            wait_seconds = self._wait_seconds(task, effective_now)
            accumulator.queued_count += 1
            accumulator.total_wait_seconds += wait_seconds
            accumulator.longest_wait_seconds = max(
                accumulator.longest_wait_seconds,
                wait_seconds,
            )
            accumulator.last_wait_reason = task.last_wait_reason

        return {
            project_id: ProjectWaitMetrics(
                project_id=accumulator.project_id,
                queued_count=accumulator.queued_count,
                started_count=accumulator.started_count,
                total_wait_seconds=accumulator.total_wait_seconds,
                longest_wait_seconds=accumulator.longest_wait_seconds,
                last_wait_reason=accumulator.last_wait_reason,
            )
            for project_id, accumulator in accumulators.items()
        }

    def _record_started_wait(self, task: ScheduledTask) -> None:
        project_id = task.project_id
        self._started_wait_totals[project_id] = (
            self._started_wait_totals.get(project_id, 0.0) + task.total_wait_seconds
        )
        self._started_wait_longest[project_id] = max(
            self._started_wait_longest.get(project_id, 0.0),
            task.total_wait_seconds,
        )
        self._started_wait_counts[project_id] = self._started_wait_counts.get(project_id, 0) + 1
        self._last_wait_reasons[project_id] = task.last_wait_reason

    def _aging_windows(self, task: ScheduledTask, now: datetime) -> int:
        if task.enqueued_at is None:
            return 0
        waited = now - task.enqueued_at
        if waited <= self._aging_threshold:
            return 0
        return int(waited // self._aging_threshold)

    @staticmethod
    def _wait_seconds(task: ScheduledTask, now: datetime) -> float:
        if task.enqueued_at is None:
            return task.total_wait_seconds
        return max(0.0, (now - task.enqueued_at).total_seconds())

    @staticmethod
    def _accumulator_for(
        accumulators: dict[str, _WaitAccumulator],
        project_id: str,
    ) -> _WaitAccumulator:
        if project_id not in accumulators:
            accumulators[project_id] = _WaitAccumulator(project_id=project_id)
        return accumulators[project_id]
