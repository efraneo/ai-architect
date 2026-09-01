"""
=========================================================
Documentation Builder

Documentation Planning Builder
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


class DocumentationBuilder:
    """
    Generates documentation improvement tasks.

    Responsibilities

        • Missing docstrings

        • API documentation

        • README improvements

        • Architecture documentation

        • Type hint completion

    This builder never modifies documentation.

    It only creates executable tasks.
    """

    ##################################################################

    def build(
        self,
        context: AIContext,
    ) -> list[PlannerTask]:

        tasks: list[PlannerTask] = []

        metrics = context.metrics

        ###############################################################
        # Missing docstrings
        ###############################################################

        undocumented = metrics.get(
            "undocumented_objects",
            0,
        )

        if undocumented:
            tasks.append(
                TaskFactory.create(
                    title="Generate missing docstrings",
                    description=(f"{undocumented} documented objects are missing."),
                    priority=TaskPriority.LOW,
                    assigned_agent="DocumentationAgent",
                    estimated_seconds=600,
                    metadata={
                        "count": undocumented,
                        "category": "documentation",
                    },
                )
            )

        ###############################################################
        # README
        ###############################################################

        if metrics.get(
            "missing_readme",
            False,
        ):
            tasks.append(
                TaskFactory.create(
                    title="Improve README",
                    description=("Repository README should be updated."),
                    priority=TaskPriority.LOW,
                    assigned_agent="DocumentationAgent",
                    estimated_seconds=300,
                    metadata={
                        "category": "documentation",
                    },
                )
            )

        ###############################################################
        # API Documentation
        ###############################################################

        api_docs = metrics.get(
            "missing_api_docs",
            0,
        )

        if api_docs:
            tasks.append(
                TaskFactory.create(
                    title="Generate API documentation",
                    description=("Public API requires documentation."),
                    priority=TaskPriority.LOW,
                    assigned_agent="DocumentationAgent",
                    estimated_seconds=600,
                    metadata={
                        "count": api_docs,
                        "category": "documentation",
                    },
                )
            )

        ###############################################################
        # Architecture documentation
        ###############################################################

        if metrics.get(
            "architecture_changed",
            False,
        ):
            tasks.append(
                TaskFactory.create(
                    title="Update architecture documentation",
                    description=(
                        "Architecture diagrams and documentation must be synchronized."
                    ),
                    priority=TaskPriority.MEDIUM,
                    assigned_agent="ArchitectureAgent",
                    estimated_seconds=900,
                    metadata={
                        "category": "documentation",
                    },
                )
            )

        ###############################################################
        # Type hints
        ###############################################################

        missing_types = metrics.get(
            "missing_type_hints",
            0,
        )

        if missing_types:
            tasks.append(
                TaskFactory.create(
                    title="Complete type annotations",
                    description=("Add missing Python type hints."),
                    priority=TaskPriority.LOW,
                    assigned_agent="CodeReviewerAgent",
                    estimated_seconds=600,
                    metadata={
                        "count": missing_types,
                        "category": "documentation",
                    },
                )
            )

        return tasks
