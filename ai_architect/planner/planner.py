"""
=========================================================
Planner

Execution Plan Orchestrator
=========================================================
"""

from __future__ import annotations

from ai_architect.core.context import AIContext
from ai_architect.planner.builders import (
    ArchitectureBuilder,
    DependencyBuilder,
    DocumentationBuilder,
    SecurityBuilder,
    TestingBuilder,
)
from ai_architect.planner.dependency_solver import (
    DependencySolver,
)
from ai_architect.planner.models import (
    ExecutionPlan,
    PlannerTask,
)


class Planner:
    """
    Central execution planner.

    Responsibilities

        • Coordinate task builders

        • Aggregate generated tasks

        • Resolve dependencies

        • Produce the final ExecutionPlan

    This class never contains business rules.

    All planning rules belong to individual builders.
    """

    ###############################################################

    def __init__(
        self,
    ) -> None:

        self.builders = (
            ArchitectureBuilder(),
            SecurityBuilder(),
            TestingBuilder(),
            DocumentationBuilder(),
            DependencyBuilder(),
        )

        self.dependency_solver = DependencySolver()

    ###############################################################

    def build_plan(
        self,
        context: AIContext,
    ) -> ExecutionPlan:

        tasks: list[PlannerTask] = []

        #
        # Execute every builder
        #

        for builder in self.builders:
            tasks.extend(
                builder.build(
                    context,
                )
            )

        #
        # Resolve dependency order
        #

        ordered = self.dependency_solver.resolve(
            tasks,
        )

        return ExecutionPlan(
            tasks=ordered,
        )

    ###############################################################

    def summary(
        self,
        plan: ExecutionPlan,
    ) -> dict:

        return {
            "tasks": plan.total_tasks,
            "completed": plan.completed_tasks,
            "pending": plan.pending_tasks,
            "progress": plan.progress,
        }

    ###############################################################

    def empty(
        self,
        context: AIContext,
    ) -> bool:

        return (
            self.build_plan(
                context,
            ).total_tasks
            == 0
        )

    ###############################################################

    def builders_count(
        self,
    ) -> int:

        return len(
            self.builders,
        )
