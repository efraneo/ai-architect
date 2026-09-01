"""
=========================================================
Dependency Builder

Dependency Planning Builder
=========================================================
"""

from __future__ import annotations

from ai_architect.core.context import AIContext
from ai_architect.planner.models import (
    PlannerTask,
    TaskPriority,
)
from ai_architect.planner.task import (
    TaskFactory,
)


class DependencyBuilder:
    """
    Generates dependency-related tasks.

    Responsibilities

        • Circular imports

        • Broken dependencies

        • Dependency updates

        • Dependency graph cleanup

        • Import optimization

    This builder never modifies the repository.

    It only generates executable tasks.
    """

    ##################################################################

    def build(
        self,
        context: AIContext,
    ) -> list[PlannerTask]:

        tasks: list[PlannerTask] = []

        metrics = context.metrics

        ###############################################################
        # Circular imports
        ###############################################################

        circular = metrics.get(
            "circular_dependencies",
            0,
        )

        if circular:
            tasks.append(
                TaskFactory.create(
                    title="Resolve circular dependencies",
                    description=(f"{circular} circular dependencies detected."),
                    priority=TaskPriority.HIGH,
                    assigned_agent="DependencyAgent",
                    estimated_seconds=900,
                    metadata={
                        "count": circular,
                        "category": "dependency",
                    },
                )
            )

        ###############################################################
        # Dependency updates
        ###############################################################

        outdated = metrics.get(
            "outdated_dependencies",
            0,
        )

        if outdated:
            tasks.append(
                TaskFactory.create(
                    title="Update outdated dependencies",
                    description=(f"{outdated} packages require updates."),
                    priority=TaskPriority.MEDIUM,
                    assigned_agent="DependencyAgent",
                    estimated_seconds=900,
                    metadata={
                        "count": outdated,
                        "category": "dependency",
                    },
                )
            )

        ###############################################################
        # Vulnerable dependencies
        ###############################################################

        vulnerable = metrics.get(
            "dependency_vulnerabilities",
            0,
        )

        if vulnerable:
            tasks.append(
                TaskFactory.create(
                    title="Patch vulnerable dependencies",
                    description=("Dependencies contain known vulnerabilities."),
                    priority=TaskPriority.CRITICAL,
                    assigned_agent="SecurityAgent",
                    estimated_seconds=1200,
                    metadata={
                        "count": vulnerable,
                        "category": "dependency",
                    },
                )
            )

        ###############################################################
        # Broken imports
        ###############################################################

        broken = metrics.get(
            "broken_imports",
            0,
        )

        if broken:
            tasks.append(
                TaskFactory.create(
                    title="Repair broken imports",
                    description=("Repository contains invalid imports."),
                    priority=TaskPriority.HIGH,
                    assigned_agent="DependencyAgent",
                    estimated_seconds=600,
                    metadata={
                        "count": broken,
                        "category": "dependency",
                    },
                )
            )

        ###############################################################
        # Dependency graph
        ###############################################################

        graph = metrics.get(
            "dependency_graph_warnings",
            0,
        )

        if graph:
            tasks.append(
                TaskFactory.create(
                    title="Optimize dependency graph",
                    description=("Dependency graph requires cleanup."),
                    priority=TaskPriority.MEDIUM,
                    assigned_agent="ArchitectureAgent",
                    estimated_seconds=900,
                    metadata={
                        "count": graph,
                        "category": "dependency",
                    },
                )
            )

        return tasks
