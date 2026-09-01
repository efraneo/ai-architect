"""
=========================================================
Code Reviewer
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.analyzer.complexity_analyzer import (
    ComplexityAnalyzer,
)

from .models import (
    ReviewIssue,
    ReviewReport,
    Severity,
)


class CodeReviewer:
    def __init__(self):

        self.complexity = ComplexityAnalyzer()

    def review(
        self,
        file: str | Path,
    ) -> ReviewReport:

        path = Path(file)

        report = ReviewReport()

        lines = path.read_text(encoding="utf-8").splitlines()

        if len(lines) > 600:
            report.add(
                ReviewIssue(
                    file=str(path),
                    line=0,
                    severity=Severity.CRITICAL,
                    rule="MAX_FILE_LINES",
                    message=("Archivo supera 600 líneas."),
                )
            )

        complexity = self.complexity.score(path)

        if complexity > 10:
            report.add(
                ReviewIssue(
                    file=str(path),
                    line=0,
                    severity=Severity.WARNING,
                    rule="COMPLEXITY",
                    message=(f"Complejidad {complexity}"),
                )
            )

        if not lines:
            report.add(
                ReviewIssue(
                    file=str(path),
                    line=0,
                    severity=Severity.INFO,
                    rule="EMPTY_FILE",
                    message="Archivo vacío.",
                )
            )

        report.score = max(
            0.0,
            100.0 - (report.total_issues * 5),
        )

        return report
