"""
Project Manager Agent

Coordinates project analysis and planning.
"""

from __future__ import annotations

from ai_architect.analyzer.models import ProjectAnalysis
from ai_architect.analyzer.project_analyzer import ProjectAnalyzer
from ai_architect.core.context import AIContext
from ai_architect.core.context_builder import AnalysisContextBuilder
from ai_architect.planner.models import ExecutionPlan
from ai_architect.planner.planner import Planner


class ProjectManagerAgent:
    """Coordinates repository analysis and execution planning."""

    def __init__(self) -> None:
        self.analyzer = ProjectAnalyzer()
        self.context_builder = AnalysisContextBuilder()
        self.planner = Planner()

    def analyze(
        self,
        project: str,
    ) -> ProjectAnalysis:
        """Analyze a repository."""

        return self.analyzer.analyze(
            project,
        )

    def build_context(
        self,
        project: str,
        analysis: ProjectAnalysis,
    ) -> AIContext:
        """Build the shared AIContext."""

        return self.context_builder.build_and_validate(
            project,
            analysis,
        )

    def plan(
        self,
        project: str,
    ) -> ExecutionPlan:
        """Analyze the project and build its execution plan."""

        analysis = self.analyze(
            project,
        )

        context = self.build_context(
            project,
            analysis,
        )

        return self.planner.build_plan(
            context,
        )
