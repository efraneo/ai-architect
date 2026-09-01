"""
Analysis Context Builder

Institutional Adapter
"""

from __future__ import annotations

from typing import Any

from ai_architect.analyzer.models import ProjectAnalysis
from ai_architect.core.context import AIContext


class AnalysisContextBuilder:
    """
    Converts ProjectAnalysis into the shared AIContext.

    This adapter keeps the Analyzer and Planner subsystems
    decoupled from each other's internal models.
    """

    def build(
        self,
        repository: str,
        analysis: ProjectAnalysis,
    ) -> AIContext:
        """Build an AIContext from ProjectAnalysis."""

        context = AIContext(
            repository=str(repository),
        )

        self._populate_analysis(
            context,
            analysis,
        )

        self._populate_task(
            context,
            analysis,
        )

        self._populate_metrics(
            context,
            analysis,
        )

        self._populate_memory(
            context,
            analysis,
        )

        self._populate_data(
            context,
            analysis,
        )

        return context

    # =====================================================
    # Analysis
    # =====================================================

    def _populate_analysis(
        self,
        context: AIContext,
        analysis: ProjectAnalysis,
    ) -> None:
        summary = analysis.summary

        context.analysis = {
            "summary": {
                "total_files": summary.total_files,
                "python_files": summary.python_files,
                "total_classes": summary.total_classes,
                "total_functions": summary.total_functions,
                "dependency_modules": summary.dependency_modules,
                "duplicate_groups": summary.duplicate_groups,
                "average_complexity": summary.average_complexity,
            },
            "files": list(analysis.files),
            "dependencies": dict(analysis.dependencies),
            "duplicates": list(analysis.duplicates),
            "recommendations": list(
                analysis.recommendations,
            ),
        }

    # =====================================================
    # Metrics
    # =====================================================

    def _populate_metrics(
        self,
        context: AIContext,
        analysis: ProjectAnalysis,
    ) -> None:
        context.update_metrics(
            dict(analysis.metrics),
        )

    # =====================================================
    # Memory
    # =====================================================

    def _populate_memory(
        self,
        context: AIContext,
        analysis: ProjectAnalysis,
    ) -> None:
        context.memory = {
            "recommendations": list(
                analysis.recommendations,
            ),
            "duplicate_groups": (analysis.summary.duplicate_groups),
            "average_complexity": (analysis.summary.average_complexity),
        }

    # =====================================================
    # Generic Data
    # =====================================================

    def _populate_data(
        self,
        context: AIContext,
        analysis: ProjectAnalysis,
    ) -> None:
        context.put(
            "project_analysis",
            analysis,
        )

        context.put(
            "analysis_summary",
            analysis.summary,
        )

        context.put(
            "analysis_recommendations",
            list(analysis.recommendations),
        )

    # =====================================================
    # Validation
    # =====================================================

    def validate(
        self,
        context: AIContext,
    ) -> bool:
        """Validate the generated context."""

        if not context.repository:
            return False

        if not isinstance(
            context.analysis,
            dict,
        ):
            return False

        if not isinstance(
            context.metrics,
            dict,
        ):
            return False

        return True

    # =====================================================
    # Build + Validate
    # =====================================================

    def build_and_validate(
        self,
        repository: str,
        analysis: ProjectAnalysis,
    ) -> AIContext:
        """Build and validate an AIContext."""

        context = self.build(
            repository,
            analysis,
        )

        if not self.validate(context):
            raise ValueError(
                "Generated AIContext failed validation.",
            )

        return context

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        context: AIContext,
    ) -> dict[str, Any]:
        """Return a compact context summary."""

        return {
            "repository": context.repository,
            "analysis": bool(context.analysis),
            "metrics": len(context.metrics),
            "memory": bool(context.memory),
            "data": len(context.data),
        }

    # =====================================================
    # Task
    # =====================================================

    def _populate_task(
        self,
        context: AIContext,
        analysis: ProjectAnalysis,
    ) -> None:
        context.task = {
            "project": context.repository,
            "analysis": analysis,
            "summary": analysis.summary,
            "recommendations": list(
                analysis.recommendations,
            ),
            "metrics": dict(
                analysis.metrics,
            ),
        }


# =========================================================
# Convenience API
# =========================================================


def build_context(
    repository: str,
    analysis: ProjectAnalysis,
) -> AIContext:
    """Build and validate a project analysis context."""

    builder = AnalysisContextBuilder()

    return builder.build_and_validate(
        repository,
        analysis,
    )
