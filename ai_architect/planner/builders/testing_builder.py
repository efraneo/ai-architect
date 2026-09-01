"""
=========================================================
Testing Builder

Testing Planning Builder
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


class TestingBuilder:
    """
    Generates testing and validation tasks.

    Responsibilities

        • Unit tests

        • Integration tests

        • Coverage

        • Regression tests

        • Validation findings

        • Test failures

    This builder only generates tasks.
    """

    ##################################################################

    def build(
        self,
        context: AIContext,
    ) -> list[PlannerTask]:

        tasks: list[PlannerTask] = []

        metrics = context.metrics

        tests = context.tests

        validation = context.validation

        ###############################################################
        # Failed Tests
        ###############################################################

        if not tests.get(
            "success",
            True,
        ):
            tasks.append(
                TaskFactory.create(
                    title="Fix failing tests",
                    description=("Repository contains failing automated tests."),
                    priority=TaskPriority.CRITICAL,
                    assigned_agent="TestingAgent",
                    estimated_seconds=900,
                    metadata={
                        "category": "testing",
                    },
                )
            )

        ###############################################################
        # Coverage
        ###############################################################

        coverage = metrics.get(
            "coverage",
            metrics.get(
                "coverage_estimate",
                100,
            ),
        )

        if coverage < 80:
            tasks.append(
                TaskFactory.create(
                    title="Increase test coverage",
                    description=(f"Current coverage is {coverage:.1f}%."),
                    priority=TaskPriority.MEDIUM,
                    assigned_agent="TestingAgent",
                    estimated_seconds=1200,
                    metadata={
                        "coverage": coverage,
                        "category": "testing",
                    },
                )
            )

        ###############################################################
        # Validation Findings
        ###############################################################

        findings = validation.get(
            "findings",
            [],
        )

        if findings:
            tasks.append(
                TaskFactory.create(
                    title="Resolve validation findings",
                    description=(f"{len(findings)} validation issues detected."),
                    priority=TaskPriority.HIGH,
                    assigned_agent="CodeReviewerAgent",
                    estimated_seconds=600,
                    metadata={
                        "count": len(findings),
                        "category": "testing",
                    },
                )
            )

        ###############################################################
        # Missing Tests
        ###############################################################

        missing = metrics.get(
            "missing_tests",
            0,
        )

        if missing:
            tasks.append(
                TaskFactory.create(
                    title="Create missing tests",
                    description=(f"{missing} modules lack automated tests."),
                    priority=TaskPriority.MEDIUM,
                    assigned_agent="TestingAgent",
                    estimated_seconds=900,
                    metadata={
                        "count": missing,
                        "category": "testing",
                    },
                )
            )

        ###############################################################
        # Regression Suite
        ###############################################################

        regression = metrics.get(
            "regression_risk",
            False,
        )

        if regression:
            tasks.append(
                TaskFactory.create(
                    title="Execute regression suite",
                    description=("Repository requires regression validation."),
                    priority=TaskPriority.HIGH,
                    assigned_agent="TestingAgent",
                    estimated_seconds=1200,
                    metadata={
                        "category": "testing",
                    },
                )
            )

        ###############################################################
        # Performance Tests
        ###############################################################

        performance = metrics.get(
            "performance_tests",
            False,
        )

        if performance:
            tasks.append(
                TaskFactory.create(
                    title="Run performance tests",
                    description=("Performance verification recommended."),
                    priority=TaskPriority.MEDIUM,
                    assigned_agent="PerformanceAgent",
                    estimated_seconds=1200,
                    metadata={
                        "category": "testing",
                    },
                )
            )

        return tasks
