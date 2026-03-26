"""Progress Tracker for chatforge.

Thread-safe tracker for multi-step agent tasks. Reports progress
as plain dict snapshots suitable for SSE streaming to the browser.

No domain-specific assumptions — works for any task that has a
total count and individual items that start, complete, or fail.

Usage:
    from chatforge.services.progress import ProgressTracker

    tracker = ProgressTracker()
    tracker.set_total(13)

    tracker.on_task_started("slide_0", "Processing first item")
    tracker.on_task_completed("slide_0", "Done")

    snapshot = tracker.to_dict()
    # {"total": 13, "completed": 1, "failed": 0, ...}
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TaskInfo:
    """State of one tracked task."""

    task_id: str
    description: str = ""
    status: str = "running"
    result: str = ""
    error: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class ProgressTracker:
    """Track progress of multi-step agent tasks.

    Thread-safe. Call from the agent stream (which may run in a
    thread pool) and read from the SSE handler (async).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total: int = 0
        self._tasks: dict[str, TaskInfo] = {}
        self._completed: int = 0
        self._failed: int = 0
        self._active_task_id: str | None = None

    @property
    def active(self) -> bool:
        """True if tracking is active (total > 0 and not all done)."""
        with self._lock:
            return self._total > 0 and (self._completed + self._failed) < self._total

    def set_total(self, total: int) -> None:
        """Set the total number of items to process.

        Can be called multiple times (e.g., if the agent discovers
        the total mid-run).
        """
        with self._lock:
            self._total = total
        logger.debug("Progress total set to %d", total)

    def on_task_started(self, task_id: str, description: str = "") -> None:
        """Mark a task as started.

        Args:
            task_id: Unique identifier for this task.
            description: Human-readable description.
        """
        with self._lock:
            self._tasks[task_id] = TaskInfo(
                task_id=task_id,
                description=description,
            )
            self._active_task_id = task_id
        logger.debug("Task started: %s — %s", task_id, description)

    def on_task_completed(self, task_id: str, result: str = "") -> None:
        """Mark a task as completed.

        Args:
            task_id: The task that completed.
            result: Brief result summary.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = "completed"
                task.result = result
                task.completed_at = datetime.now(timezone.utc)
            self._completed += 1
            if self._active_task_id == task_id:
                self._active_task_id = None
        logger.debug("Task completed: %s (%d/%d)", task_id, self._completed, self._total)

    def on_task_failed(self, task_id: str, error: str = "") -> None:
        """Mark a task as failed.

        Args:
            task_id: The task that failed.
            error: Error description.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = "failed"
                task.error = error
                task.completed_at = datetime.now(timezone.utc)
            self._failed += 1
            if self._active_task_id == task_id:
                self._active_task_id = None
        logger.debug("Task failed: %s — %s", task_id, error)

    def reset(self) -> None:
        """Reset all progress state for a new run."""
        with self._lock:
            self._total = 0
            self._tasks.clear()
            self._completed = 0
            self._failed = 0
            self._active_task_id = None

    def to_dict(self) -> dict[str, Any]:
        """Snapshot of progress state for SSE/API responses.

        Returns a plain dict suitable for JSON serialization:
        {
            "total": 13,
            "completed": 5,
            "failed": 0,
            "active_task": "task_6",
            "active_description": "Processing item 6",
            "percent": 38,
            "tasks": [
                {"task_id": "task_1", "status": "completed", ...},
                ...
            ]
        }
        """
        with self._lock:
            done = self._completed + self._failed
            percent = round((done / self._total) * 100) if self._total > 0 else 0

            active_desc = ""
            if self._active_task_id and self._active_task_id in self._tasks:
                active_desc = self._tasks[self._active_task_id].description

            return {
                "total": self._total,
                "completed": self._completed,
                "failed": self._failed,
                "active_task": self._active_task_id,
                "active_description": active_desc,
                "percent": percent,
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "description": t.description,
                        "status": t.status,
                        "result": t.result[:200] if t.result else "",
                        "error": t.error[:200] if t.error else "",
                    }
                    for t in self._tasks.values()
                ],
            }
