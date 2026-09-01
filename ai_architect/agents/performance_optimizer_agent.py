"""
=========================================================
Performance Optimizer Agent
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .base_agent import BaseAgent


class PerformanceOptimizerAgent(BaseAgent):
    name = "Performance Optimizer"

    RULES = (
        ".iterrows(",
        "range(len(",
        ".append(",
    )

    def review(
        self,
        project: str,
    ) -> dict:

        improvements = []

        for file in Path(project).rglob("*.py"):
            source = file.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            for rule in self.RULES:
                if rule in source:
                    improvements.append(
                        {
                            "file": str(file),
                            "rule": rule,
                        }
                    )

        return {
            "recommendations": improvements,
            "count": len(improvements),
        }
