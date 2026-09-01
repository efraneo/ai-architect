"""
Review Engine.

Coordinates the complete review subsystem.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ai_architect.reviewer.code_reviewer import CodeReviewer
from ai_architect.reviewer.models import ReviewIssue, ReviewReport, Severity
from ai_architect.reviewer.review_report import ReviewReportFormatter
from ai_architect.reviewer.review_state import ReviewStateMixin
from ai_architect.workspace.workspace_loader import WorkspaceLoader


class ReviewEngine(ReviewStateMixin):
    """Main coordinator for repository code reviews."""

    def __init__(self) -> None:
        self.loader = WorkspaceLoader()
        self.reviewer = CodeReviewer()
        self.formatter = ReviewReportFormatter()
        self.reviewed_files = 0
        self.last_report = None

    def review(
        self,
        repository: str | Path,
    ) -> ReviewReport:
        """Review every Python file in a repository."""
        repository = Path(repository).resolve()
        workspace = self.loader.load(repository)
        report = ReviewReport()

        python_files = [
            Path(file.path) for file in workspace.files if file.extension == ".py"
        ]

        total_score = 0.0
        reviewed = 0

        for file in python_files:
            try:
                file_report = self.reviewer.review(file)
            except Exception as exc:
                report.add(
                    ReviewIssue(
                        file=str(file),
                        line=0,
                        severity=Severity.ERROR,
                        rule="REVIEW_EXCEPTION",
                        message=str(exc),
                    )
                )
                continue

            total_score += file_report.score
            reviewed += 1
            report.issues.extend(file_report.issues)

        report.score = (
            round(
                total_score / reviewed,
                2,
            )
            if reviewed
            else 0.0
        )

        self.reviewed_files = reviewed
        self.last_report = report

        self._export(
            repository,
            report,
        )

        return report

    def _export(
        self,
        repository: Path,
        report: ReviewReport,
    ) -> None:
        """Export the review in JSON and Markdown formats."""
        folder = repository / ".ai_architect"
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._export_json(
            folder,
            report,
        )
        self._export_markdown(
            folder,
            report,
        )

    def _export_json(
        self,
        folder: Path,
        report: ReviewReport,
    ) -> None:
        """Export the report as JSON."""
        target = folder / "review.json"

        data = {
            "score": report.score,
            "approved": report.approved,
            "total_issues": report.total_issues,
            "critical": self._count(
                report,
                Severity.CRITICAL,
            ),
            "errors": self._count(
                report,
                Severity.ERROR,
            ),
            "warnings": self._count(
                report,
                Severity.WARNING,
            ),
            "info": self._count(
                report,
                Severity.INFO,
            ),
            "issues": [
                {
                    "file": issue.file,
                    "line": issue.line,
                    "severity": issue.severity.value,
                    "rule": issue.rule,
                    "message": issue.message,
                }
                for issue in report.issues
            ],
        }

        target.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _export_markdown(
        self,
        folder: Path,
        report: ReviewReport,
    ) -> None:
        """Export the report as Markdown."""
        target = folder / "review.md"
        markdown = [
            "# QUANT AI Architect Review",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|------:|",
            f"| Score | {report.score:.2f} |",
            f"| Approved | {report.approved} |",
            f"| Total Issues | {report.total_issues} |",
            f"| Critical | {self._count(report, Severity.CRITICAL)} |",
            f"| Errors | {self._count(report, Severity.ERROR)} |",
            f"| Warnings | {self._count(report, Severity.WARNING)} |",
            f"| Info | {self._count(report, Severity.INFO)} |",
            "",
            "## Issues",
            "",
        ]

        if not report.issues:
            markdown.append("No issues found.")
        else:
            current_file = None

            for issue in sorted(
                report.issues,
                key=lambda item: (
                    item.file,
                    item.line,
                ),
            ):
                if current_file != issue.file:
                    current_file = issue.file
                    markdown.extend(
                        [
                            "",
                            f"### {current_file}",
                            "",
                        ]
                    )

                markdown.extend(
                    [
                        "- "
                        f"**[{issue.severity.value}]** "
                        f"Line **{issue.line}** "
                        f"**{issue.rule}**",
                        f"  - {issue.message}",
                    ]
                )

        markdown.extend(
            [
                "",
                "---",
                "",
                "Generated by QUANT AI Architect",
            ]
        )

        target.write_text(
            "\n".join(markdown),
            encoding="utf-8",
        )

    @staticmethod
    def _count(
        report: ReviewReport,
        severity: Severity,
    ) -> int:
        return sum(1 for issue in report.issues if issue.severity == severity)

    @staticmethod
    def issues_by_severity(
        report: ReviewReport,
        severity: Severity,
    ) -> list[ReviewIssue]:
        return [issue for issue in report.issues if issue.severity == severity]

    def statistics(
        self,
        report: ReviewReport | None = None,
    ) -> dict:
        """Return the statistics for ``report``, or for the last review.

        Both forms are in use: ``commands/review.py`` and :meth:`to_dict` pass
        an explicit report, while :class:`Reviewer` calls it with no arguments
        and expects the numbers of the last review. Before, this was a
        staticmethod that required ``report``, so the no-argument call raised
        ``TypeError`` at runtime.
        """
        if report is None:
            return super().statistics()

        return {
            "reviewed": self.reviewed_files,
            "score": report.score,
            "approved": report.approved,
            "total": report.total_issues,
            "critical": self._count(report, Severity.CRITICAL),
            "errors": self._count(report, Severity.ERROR),
            "warnings": self._count(report, Severity.WARNING),
            "info": self._count(report, Severity.INFO),
        }

    def to_dict(
        self,
        report: ReviewReport,
    ) -> dict:
        data = asdict(report)
        data["approved"] = report.approved
        data["total_issues"] = report.total_issues
        data["statistics"] = self.statistics(report)
        return data
