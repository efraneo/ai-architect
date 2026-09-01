"""
=========================================================
Analyze Command

CLI adapter for the Analysis Engine.
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.analyzer.analysis_engine import (
    AnalysisEngine,
)


def run(
    project: str,
) -> dict:
    """
    Executes a complete repository analysis.

    Parameters
    ----------
    project:
        Repository root.

    Returns
    -------
    dict
        Serializable analysis report.
    """

    repository = Path(
        project,
    ).resolve()

    if not repository.exists():
        return {
            "success": False,
            "error": "Repository not found.",
            "repository": str(
                repository,
            ),
        }

    try:
        engine = AnalysisEngine()

        analysis = engine.analyze(
            repository,
        )

        summary = analysis.summary

        return {
            "success": True,
            "repository": str(
                repository,
            ),
            "summary": {
                "total_files": summary.total_files,
                "python_files": summary.python_files,
                "total_classes": summary.total_classes,
                "total_functions": summary.total_functions,
                "dependency_modules": summary.dependency_modules,
                "duplicate_groups": summary.duplicate_groups,
                "average_complexity": summary.average_complexity,
            },
            "metrics": analysis.metrics,
            "recommendations": analysis.recommendations,
        }

    except Exception as exc:
        return {
            "success": False,
            "repository": str(
                repository,
            ),
            "error": str(
                exc,
            ),
        }
