"""
=========================================================
Report Formatter
=========================================================
"""

from __future__ import annotations

from datetime import datetime


class ReportFormatter:
    def format(
        self,
        report: dict,
    ) -> str:

        lines = [
            "🤖 QUANT AI ARCHITECT",
            "",
            f"Fecha: {datetime.now()}",
            "",
        ]

        for key, value in report.items():
            lines.append(f"• {key}: {value}")

        return "\n".join(lines)
