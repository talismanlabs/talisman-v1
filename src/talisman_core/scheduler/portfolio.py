"""Portfolio scheduler (slice S11.01).

Caps the number of concurrently active worker slots across all projects (default 3,
per architecture decision D8). Tasks are enqueued and started in priority-then-FIFO
order; the scheduler never lets more than the slot limit run at once. Wait-time
tracking and aging promotion are added in S11.02.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScheduledTask:
    """A unit of work waiting for, or holding, a worker slot."""

    task_id: str
    project_id: str
    priority: int = 0  # higher starts first; ties are broken FIFO (enqueue order)


class PortfolioScheduler:
    """Enforce the active worker-slot cap across queued tasks."""

    def __init__(self, active_slot_limit: int = 3) -> None:
        """Create a scheduler with the given active-slot cap (must be >= 1)."""
        if active_slot_limit < 1:
            raise ValueError("active_slot_limit must be at least 1.")
        self._limit = active_slot_limit
        self._queued: list[ScheduledTask] = []
        self._active: dict[str, ScheduledTask] = {}

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

    def enqueue(self, task: ScheduledTask) -> None:
        """Add a task to the wait queue."""
        self._queued.append(task)

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
        self._active[task.task_id] = task
        return task

    def complete(self, task_id: str) -> None:
        """Free the worker slot held by an active task (no-op if not active)."""
        self._active.pop(task_id, None)
