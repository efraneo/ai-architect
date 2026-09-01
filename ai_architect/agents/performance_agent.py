"""
=========================================================
Performance Agent
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .base_agent import BaseAgent


class PerformanceAgent(BaseAgent):
    name = "Performance Agent"

    def review(
        self,
        project: str,
    ) -> dict:

        issues = []

        for file in Path(project).rglob("*.py"):
            source = file.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            if ".iterrows(" in source:
                issues.append(f"{file}: iterrows")

            if "for i in range(len(" in source:
                issues.append(f"{file}: range(len())")

        return {
            "performance_issues": issues,
            "total": len(issues),
        }
