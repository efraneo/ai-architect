# Parte 1

"""
=========================================================
Review Command

CLI adapter for the Review Engine.
=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.reviewer.review_engine import (
    ReviewEngine,
)


def run(
    project: str,
) -> dict:
    """
    Executes a complete repository review.

    Parameters
    ----------
    project:
        Repository root.

    Returns
    -------
    dict
        Serializable review report.
    """

    repository = Path(
        project,
    ).resolve()

    if not repository.exists():
        return {
            "success": False,
            "repository": str(
                repository,
            ),
            "error": "Repository not found.",
        }

    try:
        engine = ReviewEngine()

        report = engine.review(
            repository,
        )

        statistics = engine.statistics(
            report,
        )

        result: dict[str, Any] = {
            "success": True,
            "repository": str(
                repository,
            ),
            "approved": report.approved,
            "score": report.score,
            "total_issues": report.total_issues,
            "statistics": statistics,
            "issues": [],
        }

        for issue in report.issues:
            result["issues"].append(
                {
                    "file": issue.file,
                    "line": issue.line,
                    "severity": issue.severity.value,
                    "rule": issue.rule,
                    "message": issue.message,
                }
            )

        # Parte 2

        return result

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
