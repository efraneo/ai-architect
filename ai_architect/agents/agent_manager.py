"""
Agent Manager

Central Multi-Agent Orchestrator
"""

from __future__ import annotations

from ai_architect.agents.agent_context import AgentContext
from ai_architect.agents.architect_agent import ArchitectAgent
from ai_architect.agents.architecture_agent import ArchitectureAgent
from ai_architect.agents.code_reviewer_agent import CodeReviewerAgent
from ai_architect.agents.dependency_agent import DependencyAgent
from ai_architect.agents.documentation_agent import DocumentationAgent
from ai_architect.agents.git_agent import GitAgent
from ai_architect.agents.license_agent import LicenseAgent
from ai_architect.agents.project_metrics_agent import ProjectMetricsAgent
from ai_architect.agents.refactor_agent import RefactorAgent
from ai_architect.agents.security_agent import SecurityAgent
from ai_architect.agents.test_agent import TestAgent
from ai_architect.agents.testing_agent import TestingAgent


class AgentManager:
    """
    Central orchestrator of QUANT AI Architect.

    Phase 1:
        Static repository inspection

    Phase 2:
        AI analysis

    Phase 3:
        Return unified execution context
    """

    def __init__(self) -> None:
        # Static agents
        self.metrics = ProjectMetricsAgent()
        self.architecture = ArchitectureAgent()
        self.testing = TestingAgent()
        self.security = SecurityAgent()
        self.dependencies = DependencyAgent()
        self.licenses = LicenseAgent()
        self.git = GitAgent()

        # AI agents
        self.architect = ArchitectAgent()
        self.refactor = RefactorAgent()
        self.reviewer = CodeReviewerAgent()
        self.tests = TestAgent()
        self.documentation = DocumentationAgent()

    def execute(
        self,
        repository: str,
    ) -> AgentContext:
        context = AgentContext(repository)

        # -------------------------------------------------
        # STATIC ANALYSIS
        # -------------------------------------------------

        context.set(
            "metrics",
            self.metrics.review(repository),
        )

        context.set(
            "architecture",
            self.architecture.review(repository),
        )

        context.set(
            "testing",
            self.testing.review(repository),
        )

        context.set(
            "security",
            self.security.review(repository),
        )

        context.set(
            "dependencies",
            self.dependencies.review(repository),
        )

        context.set(
            "licenses",
            self.licenses.review(repository),
        )

        context.set(
            "git",
            self.git.review(repository),
        )

        # -------------------------------------------------
        # AI ANALYSIS
        # -------------------------------------------------

        architecture_report = self.architect.run(
            context.data,
        )

        context.set(
            "architect",
            architecture_report,
        )

        refactor_report = self.refactor.run(
            context.data,
        )

        context.set(
            "refactor",
            refactor_report,
        )

        review_report = self.reviewer.run(
            context.data,
        )

        context.set(
            "review",
            review_report,
        )

        testing_report = self.tests.run(
            context.data,
        )

        context.set(
            "tests",
            testing_report,
        )

        documentation_report = self.documentation.run(
            context.data,
        )

        context.set(
            "documentation",
            documentation_report,
        )

        return context

    def available_agents(self) -> list[str]:
        return [
            self.metrics.name,
            self.architecture.name,
            self.testing.name,
            self.security.name,
            self.dependencies.name,
            self.licenses.name,
            self.git.name,
            self.architect.name,
            self.refactor.name,
            self.reviewer.name,
            self.tests.name,
            self.documentation.name,
        ]

    def health(self) -> dict[str, object]:
        agents = self.available_agents()

        return {
            "agents": len(agents),
            "available": agents,
            "status": "READY",
        }

    def summary(
        self,
        context: AgentContext,
    ) -> dict:
        return context.summary()
