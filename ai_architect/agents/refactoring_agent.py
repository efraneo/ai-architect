"""
=========================================================
Refactoring Agent
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .base_agent import BaseAgent


class RefactoringAgent(BaseAgent):
    name = "Refactoring Agent"

    MAX_LINES = 600

    def review(
        self,
        project: str,
    ) -> dict:

        suggestions = []

        for file in Path(project).rglob("*.py"):
            lines = sum(
                1
                for _ in file.open(
                    encoding="utf-8",
                    errors="ignore",
                )
            )

            if lines > self.MAX_LINES:
                modules = (lines // 300) + 1

                suggestions.append(
                    {
                        "file": str(file),
                        "lines": lines,
                        "split_into": modules,
                    }
                )

        return {
            "status": "OK",
            "refactors": suggestions,
        }
