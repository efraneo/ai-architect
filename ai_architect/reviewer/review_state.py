"""State and compatibility helpers for the review subsystem."""

from __future__ import annotations

from .models import ReviewReport, Severity


class ReviewStateMixin:
    """Public state, diagnostics, and compatibility API for review."""

    def reset(self) -> None:
        """Reset the current review state."""
        self.reviewed_files = 0
        self.last_report: ReviewReport | None = None

    def summary(self) -> dict:
        """Return a compact review summary."""
        report = self.last_report

        if report is None:
            return {
                "reviewed": self.reviewed_files,
                "score": 0.0,
                "approved": False,
                "total_issues": 0,
            }

        return {
            "reviewed": self.reviewed_files,
            "score": report.score,
            "approved": report.approved,
            "total_issues": report.total_issues,
        }

    def statistics(self) -> dict:
        """Return review statistics."""
        report = self.last_report

        if report is None:
            return {
                "reviewed": self.reviewed_files,
                "score": 0.0,
                "approved": False,
                "total": 0,
                "critical": 0,
                "errors": 0,
                "warnings": 0,
                "info": 0,
            }

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

    def health(self) -> dict:
        """Return the health status of the review subsystem."""
        report = self.last_report

        return {
            "healthy": (
                report is None
                or report.approved
            ),
            "reviewed": self.reviewed_files,
            "approved": (
                report.approved
                if report is not None
                else False
            ),
        }

    def ready(self) -> bool:
        """Return whether the review subsystem is initialized."""
        return (
            hasattr(self, "loader")
            and hasattr(self, "reviewer")
            and hasattr(self, "formatter")
        )

    def configuration(self) -> dict:
        """Return review subsystem configuration."""
        return {
            "python_only": True,
            "export_json": True,
            "export_markdown": True,
            "approval_from_report": True,
        }

    def diagnostics(self) -> dict:
        """Return diagnostic information."""
        return {
            "engine": self.__class__.__name__,
            "ready": self.ready(),
            "reviewed": self.reviewed_files,
            "has_report": self.last_report is not None,
            "healthy": self.health()["healthy"],
        }

    def version(self) -> str:
        """Return the review-state API version."""
        return "1.0"

    def approved(self) -> bool:
        """Return the approval state of the last review."""
        return bool(
            self.last_report is not None
            and self.last_report.approved
        )

    def reviewed(self) -> int:
        """Return the number of reviewed files."""
        return self.reviewed_files

    def issues(self) -> int:
        """Return the number of issues in the last report."""
        if self.last_report is None:
            return 0

        return self.last_report.total_issues

    def empty(self) -> bool:
        """Return whether no review has been performed."""
        return self.reviewed_files == 0

    @staticmethod
    def _count(
        report: ReviewReport,
        severity: Severity,
    ) -> int:
        return sum(
            1
            for issue in report.issues
            if issue.severity == severity
        )
