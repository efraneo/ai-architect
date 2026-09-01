"""
=========================================================
Dependency Solver

Task Dependency Resolution Engine
=========================================================
"""

from __future__ import annotations

from collections import defaultdict, deque

from ai_architect.planner.models import (
    PlannerTask,
)


class DependencySolver:
    """
    Resolves task execution order using
    topological sorting.

    Features

        • Dependency resolution

        • Circular dependency detection

        • Execution validation

        • Ready task discovery
    """

    ##################################################################

    def resolve(
        self,
        tasks: list[PlannerTask],
    ) -> list[PlannerTask]:

        if not tasks:
            return []

        graph: dict[str, list[str]] = defaultdict(
            list,
        )

        indegree: dict[str, int] = {task.id: 0 for task in tasks}

        task_map = {task.id: task for task in tasks}

        ###############################################################

        for task in tasks:
            for dependency in task.dependencies:
                if dependency not in task_map:
                    continue

                graph[dependency].append(
                    task.id,
                )

                indegree[task.id] += 1

        ###############################################################

        queue = deque(sorted(task.id for task in tasks if indegree[task.id] == 0))

        ordered: list[PlannerTask] = []

        while queue:
            current = queue.popleft()

            ordered.append(
                task_map[current],
            )

            for neighbor in graph[current]:
                indegree[neighbor] -= 1

                if indegree[neighbor] == 0:
                    queue.append(
                        neighbor,
                    )

        ###############################################################

        if len(ordered) != len(tasks):
            remaining = {task.id for task in tasks} - {task.id for task in ordered}

            ordered.extend(
                sorted(
                    (task_map[task_id] for task_id in remaining),
                    key=lambda task: task.priority.value,
                )
            )

        return ordered

    ##################################################################

    def has_cycles(
        self,
        tasks: list[PlannerTask],
    ) -> bool:

        return len(
            self.resolve(
                tasks,
            )
        ) != len(tasks)

    ##################################################################

    def validate(
        self,
        tasks: list[PlannerTask],
    ) -> list[str]:

        errors: list[str] = []

        ids = {task.id for task in tasks}

        ###############################################################

        for task in tasks:
            for dependency in task.dependencies:
                if dependency not in ids:
                    errors.append(f"{task.title}: missing dependency {dependency}")

        ###############################################################

        if self.has_cycles(
            tasks,
        ):
            errors.append("Circular dependency detected.")

        return errors

    ##################################################################

    def ready_tasks(
        self,
        tasks: list[PlannerTask],
    ) -> list[PlannerTask]:

        completed = {task.id for task in tasks if task.completed}

        ready: list[PlannerTask] = []

        for task in tasks:
            if task.completed:
                continue

            if all(dependency in completed for dependency in task.dependencies):
                ready.append(
                    task,
                )

        return ready
