"""
=========================================================
Code Quality Agent
=========================================================
"""

from __future__ import annotations

from ai_architect.self_improvement.refactor_engine import (
    RefactorEngine,
)


class CodeQualityAgent:
    def __init__(self):

        self.engine = RefactorEngine()

    def review(
        self,
        project: str,
    ):

        oversized = self.engine.oversized_files(project)

        return {
            "oversized_files": oversized,
            "score": max(
                100 - len(oversized) * 5,
                0,
            ),
        }
