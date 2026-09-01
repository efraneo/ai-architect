"""
=========================================================
Task Factory

Planner Task Factory
=========================================================
"""

from __future__ import annotations

import uuid

from ai_architect.planner.models import (
    PlannerTask,
    TaskPriority,
)


class TaskFactory:
    """
    Factory responsible for creating PlannerTask objects.

    All PlannerTask instances should be created through
    this factory to ensure consistency across the Planner.

    Future extensions:

        • Automatic IDs
        • Metadata normalization
        • Task templates
        • Learning integration
        • Agent recommendation
        • Priority overrides
    """

    @staticmethod
    def create(
        title: str,
        description: str,
        priority: TaskPriority,
        *,
        assigned_agent: str = "",
        estimated_seconds: int = 0,
        dependencies: list[str] | None = None,
        metadata: dict | None = None,
        retries: int = 0,
    ) -> PlannerTask:

        return PlannerTask(
            id=uuid.uuid4().hex,
            title=title,
            description=description,
            priority=priority,
            assigned_agent=assigned_agent,
            estimated_seconds=estimated_seconds,
            dependencies=list(dependencies or []),
            metadata=dict(metadata or {}),
            retries=retries,
        )

    @staticmethod
    def clone(
        task: PlannerTask,
    ) -> PlannerTask:

        return PlannerTask(
            id=uuid.uuid4().hex,
            title=task.title,
            description=task.description,
            priority=task.priority,
            assigned_agent=task.assigned_agent,
            estimated_seconds=task.estimated_seconds,
            dependencies=list(task.dependencies),
            metadata=dict(task.metadata),
            retries=task.retries,
        )

    @staticmethod
    def batch(
        tasks: list[PlannerTask],
    ) -> list[PlannerTask]:

        return [
            TaskFactory.clone(
                task,
            )
            for task in tasks
        ]
