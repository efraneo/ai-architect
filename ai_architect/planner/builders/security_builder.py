"""
=========================================================
Security Builder

Security Planning Builder
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


class SecurityBuilder:
    """
    Generates repository security tasks.

    Responsibilities

        • Vulnerabilities

        • Secret leaks

        • Unsafe dependencies

        • Authentication

        • Authorization

        • Security best practices

    This builder never fixes problems.

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
        # Security Findings
        ###############################################################

        findings = metrics.get(
            "security_findings",
            0,
        )

        if findings:
            tasks.append(
                TaskFactory.create(
                    title="Resolve security findings",
                    description=(f"{findings} security issues detected."),
                    priority=TaskPriority.CRITICAL,
                    metadata={
                        "count": findings,
                        "category": "security",
                    },
                    assigned_agent="SecurityAgent",
                    estimated_seconds=900,
                )
            )

        ###############################################################
        # Secrets
        ###############################################################

        secrets = metrics.get(
            "secret_findings",
            0,
        )

        if secrets:
            tasks.append(
                TaskFactory.create(
                    title="Remove exposed secrets",
                    description=("Repository contains possible secrets."),
                    priority=TaskPriority.CRITICAL,
                    metadata={
                        "count": secrets,
                        "category": "security",
                    },
                    assigned_agent="SecurityAgent",
                    estimated_seconds=600,
                )
            )

        ###############################################################
        # Authentication
        ###############################################################

        if context.task.get(
            "authentication",
            False,
        ):
            tasks.append(
                TaskFactory.create(
                    title="Review authentication",
                    description=("Authentication logic was modified."),
                    priority=TaskPriority.HIGH,
                    metadata={
                        "category": "security",
                    },
                    assigned_agent="SecurityAgent",
                    estimated_seconds=600,
                )
            )

        ###############################################################
        # Authorization
        ###############################################################

        if context.task.get(
            "authorization",
            False,
        ):
            tasks.append(
                TaskFactory.create(
                    title="Review authorization",
                    description=("Authorization rules must be validated."),
                    priority=TaskPriority.HIGH,
                    metadata={
                        "category": "security",
                    },
                    assigned_agent="SecurityAgent",
                    estimated_seconds=600,
                )
            )

        ###############################################################
        # Dependency vulnerabilities
        ###############################################################

        dependency_issues = metrics.get(
            "dependency_vulnerabilities",
            0,
        )

        if dependency_issues:
            tasks.append(
                TaskFactory.create(
                    title="Update vulnerable dependencies",
                    description=("Dependencies require security updates."),
                    priority=TaskPriority.HIGH,
                    metadata={
                        "count": dependency_issues,
                        "category": "security",
                    },
                    assigned_agent="DependencyAgent",
                    estimated_seconds=900,
                )
            )

        ###############################################################
        # Static Analysis
        ###############################################################

        semgrep = metrics.get(
            "semgrep_findings",
            0,
        )

        if semgrep:
            tasks.append(
                TaskFactory.create(
                    title="Review static analysis findings",
                    description=("Static analysis reported security issues."),
                    priority=TaskPriority.HIGH,
                    metadata={
                        "count": semgrep,
                        "category": "security",
                    },
                    assigned_agent="SecurityAgent",
                    estimated_seconds=600,
                )
            )

        return tasks
