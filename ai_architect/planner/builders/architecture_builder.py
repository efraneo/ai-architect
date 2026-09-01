"""
=========================================================
Architecture Builder

Architecture Planning Builder
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


class ArchitectureBuilder:
    """
    Builds architecture improvement tasks.

    Responsibilities

        • Oversized modules

        • High complexity

        • Duplicate code

        • Layer violations

        • Refactoring opportunities

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

        ##################################################################
        # Oversized modules
        ##################################################################

        oversized = metrics.get(
            "oversized_files",
            [],
        )

        if oversized:
            tasks.append(
                TaskFactory.create(
                    title="Split oversized modules",
                    description=(
                        f"{len(oversized)} oversized modules require decomposition."
                    ),
                    priority=TaskPriority.HIGH,
                    metadata={
                        "files": oversized,
                        "category": "architecture",
                    },
                )
            )

        ##################################################################
        # Complexity
        ##################################################################

        complexity = metrics.get(
            "average_complexity",
            0,
        )

        if complexity >= 10:
            tasks.append(
                TaskFactory.create(
                    title="Reduce code complexity",
                    description=("Refactor high complexity modules."),
                    priority=TaskPriority.HIGH,
                    metadata={
                        "complexity": complexity,
                        "category": "architecture",
                    },
                )
            )

        ##################################################################
        # Duplicate code
        ##################################################################

        duplicates = metrics.get(
            "duplicate_groups",
            0,
        )

        if duplicates:
            tasks.append(
                TaskFactory.create(
                    title="Merge duplicated code",
                    description=("Duplicate blocks detected across repository."),
                    priority=TaskPriority.CRITICAL,
                    metadata={
                        "duplicate_groups": duplicates,
                        "category": "architecture",
                    },
                )
            )

        ##################################################################
        # Circular dependencies
        ##################################################################

        circular = metrics.get(
            "circular_dependencies",
            0,
        )

        if circular:
            tasks.append(
                TaskFactory.create(
                    title="Resolve circular dependencies",
                    description=("Architecture contains circular imports."),
                    priority=TaskPriority.HIGH,
                    metadata={
                        "count": circular,
                        "category": "architecture",
                    },
                )
            )

        ##################################################################
        # Layer violations
        ##################################################################

        violations = metrics.get(
            "layer_violations",
            0,
        )

        if violations:
            tasks.append(
                TaskFactory.create(
                    title="Fix architecture violations",
                    description=("Dependency rules were violated."),
                    priority=TaskPriority.HIGH,
                    metadata={
                        "count": violations,
                        "category": "architecture",
                    },
                )
            )

        return tasks
