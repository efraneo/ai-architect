"""
=========================================================
Review Report Formatter
=========================================================
"""

from __future__ import annotations

from .models import (
    ReviewReport,
)


class ReviewReportFormatter:
    def format(
        self,
        report: ReviewReport,
    ) -> str:

        lines = []

        lines.append("=" * 60)

        lines.append("AI ARCHITECT REVIEW REPORT")

        lines.append("=" * 60)

        lines.append(f"Score : {report.score:.1f}")

        lines.append(f"Issues: {report.total_issues}")

        lines.append(f"Approved: {report.approved}")

        lines.append("")

        for issue in report.issues:
            lines.append(f"[{issue.severity}] {issue.file}:{issue.line}")

            lines.append(issue.rule)

            lines.append(issue.message)

            lines.append("")

        return "\n".join(lines)
