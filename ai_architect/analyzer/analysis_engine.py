"""
=========================================================
Analysis Engine

Institutional Analysis Engine
=========================================================
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ai_architect.analyzer.models import (
    ProjectAnalysis,
)
from ai_architect.analyzer.project_analyzer import (
    ProjectAnalyzer,
)


class AnalysisEngine:
    """
    High-level entry point of the analysis subsystem.

    Responsibilities

        • Execute ProjectAnalyzer

        • Export reports

        • Export metrics

        • Return ProjectAnalysis
    """

    ##################################################################

    def __init__(
        self,
    ) -> None:

        self.project = ProjectAnalyzer()

    ##################################################################

    def analyze(
        self,
        repository: str | Path,
    ) -> ProjectAnalysis:

        repository = Path(repository).resolve()

        analysis = self.project.analyze(
            repository,
        )

        self._export(
            repository,
            analysis,
        )

        return analysis

    ##################################################################
    # Export
    ##################################################################

    def _export(
        self,
        repository: Path,
        analysis: ProjectAnalysis,
    ) -> None:

        folder = repository / ".ai_architect"

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._export_json(
            folder,
            analysis,
        )

        self._export_metrics(
            folder,
            analysis,
        )

        self._export_markdown(
            folder,
            analysis,
        )

    ##################################################################

    def _export_json(
        self,
        folder: Path,
        analysis: ProjectAnalysis,
    ) -> None:

        target = folder / "analysis.json"

        with target.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                asdict(analysis),
                file,
                indent=4,
                ensure_ascii=False,
            )

    ##################################################################

    def _export_metrics(
        self,
        folder: Path,
        analysis: ProjectAnalysis,
    ) -> None:

        target = folder / "metrics.json"

        with target.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                analysis.metrics,
                file,
                indent=4,
                ensure_ascii=False,
            )

    ##################################################################

    def _export_markdown(
        self,
        folder: Path,
        analysis: ProjectAnalysis,
    ) -> None:

        summary = analysis.summary

        report = f"""# QUANT AI Architect Analysis

## Summary

| Metric | Value |
|---------|------:|
| Total Files | {summary.total_files} |
| Python Files | {summary.python_files} |
| Classes | {summary.total_classes} |
| Functions | {summary.total_functions} |
| Dependency Modules | {summary.dependency_modules} |
| Duplicate Groups | {summary.duplicate_groups} |
| Average Complexity | {summary.average_complexity} |

## Recommendations

"""

        for recommendation in analysis.recommendations:
            report += f"- {recommendation}\n"

        target = folder / "analysis.md"

        target.write_text(
            report,
            encoding="utf-8",
        )
