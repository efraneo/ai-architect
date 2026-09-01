"""
=========================================================
Test Report Formatter
=========================================================
"""

from __future__ import annotations

from .models import TestReport


class TestReportFormatter:
    def format(
        self,
        report: TestReport,
    ) -> str:

        lines = [
            "=" * 60,
            "TEST REPORT",
            "=" * 60,
            f"Started : {report.started_at}",
            f"Finished: {report.finished_at}",
            "",
            f"Passed : {report.passed}",
            f"Failed : {report.failed}",
            f"Skipped: {report.skipped}",
            "",
        ]

        for test in report.tests:
            lines.append(f"[{test.status}] {test.name}")

            if test.message:
                lines.append(test.message.strip())

                lines.append("")

        return "\n".join(lines)
