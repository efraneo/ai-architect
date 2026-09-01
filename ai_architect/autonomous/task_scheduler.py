"""
Task Scheduler.
"""

from __future__ import annotations


class TaskScheduler:
    def schedule(
        self,
        tasks: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        return sorted(
            tasks,
            key=lambda task: (
                task.get(
                    "priority",
                    0,
                ),
                task.get(
                    "risk",
                    0,
                ),
            ),
            reverse=True,
        )
