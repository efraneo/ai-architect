"""
AI Architect Agent

Top-level orchestration facade.
"""

from __future__ import annotations

import os
from pathlib import Path

from ai_architect.analyzer.models import ProjectAnalysis
from ai_architect.analyzer.project_analyzer import ProjectAnalyzer
from ai_architect.core.context import AIContext
from ai_architect.core.context_builder import AnalysisContextBuilder
from ai_architect.notifier.notifier_manager import NotifierManager
from ai_architect.planner.models import ExecutionPlan
from ai_architect.planner.planner import Planner
from ai_architect.repository.repository_manager import RepositoryManager
from ai_architect.reviewer.code_reviewer import CodeReviewer
from ai_architect.test_runner.test_runner import TestRunner


class AIArchitect:
    """High-level facade for the AI Architect pipeline."""

    def __init__(
        self,
        project: str | Path,
        telegram_env: str | Path | None = None,
    ) -> None:
        self.project = Path(project).resolve()

        self.analyzer = ProjectAnalyzer()
        self.context_builder = AnalysisContextBuilder()
        self.planner = Planner()

        self.repository_manager = RepositoryManager(
            self.project,
        )

        self.reviewer = CodeReviewer()
        self.test_runner = TestRunner()

        resolved_telegram_env = (
            telegram_env
            if telegram_env is not None
            else os.getenv(
                "TELEGRAM_ENV",
                ".env",
            )
        )

        self.notifier = NotifierManager(
            resolved_telegram_env,
        )

    def analyze(self) -> ProjectAnalysis:
        """Analyze the configured project."""

        return self.analyzer.analyze(
            self.project,
        )

    def build_context(
        self,
        analysis: ProjectAnalysis,
    ) -> AIContext:
        """Convert analysis into the shared context."""

        return self.context_builder.build_and_validate(
            str(self.project),
            analysis,
        )

    def plan(
        self,
        analysis: ProjectAnalysis | None = None,
    ) -> ExecutionPlan:
        """Build an execution plan from project analysis."""

        if analysis is None:
            analysis = self.analyze()

        context = self.build_context(
            analysis,
        )

        return self.planner.build_plan(
            context,
        )

    def run_tests(
        self,
        project: str | Path | None = None,
    ):
        """Delegate test execution to TestRunner."""

        target = self.project if project is None else Path(project).resolve()

        return self.test_runner.run(
            target,
        )

    def review_file(
        self,
        file: str | Path,
    ):
        """Delegate file review to CodeReviewer."""

        return self.reviewer.review(
            Path(file),
        )

    def repository_status(self):
        """Return repository status."""

        return self.repository_manager.status.status()
