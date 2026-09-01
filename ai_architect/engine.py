"""
=========================================================
AI Architect Engine
=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.agent import AIArchitect
from ai_architect.notifier.models import NotificationLevel


class ArchitectEngine:
    """
    Main execution engine.

    Orquesta el flujo principal del AI Architect y centraliza
    el resumen de la ejecución.
    """

    def __init__(
        self,
        project: str | Path,
        telegram_env: str | Path,
    ) -> None:

        self.project = Path(project).resolve()

        self.agent = AIArchitect(
            project=self.project,
            telegram_env=telegram_env,
        )

    def execute(self) -> dict[str, Any]:

        analysis = self.agent.analyze()

        plan = self.agent.plan()

        tests = self.agent.run_tests()

        summary = self._build_summary(
            analysis,
            plan,
            tests,
        )

        self.agent.notifier.notify(
            title="Execution Finished",
            message=summary,
            level=NotificationLevel.SUCCESS,
        )

        return {
            "analysis": analysis,
            "plan": plan,
            "tests": tests,
            "summary": summary,
        }

    @staticmethod
    def _build_summary(
        analysis,
        plan,
        tests,
    ) -> str:

        return "\n".join(
            [
                "🤖 QUANT AI ARCHITECT",
                "",
                f"Files: {analysis.get('total_files', 0)}",
                f"Python Files: {analysis.get('python_files', 0)}",
                f"Tasks Planned: {getattr(plan, 'total_tasks', 0)}",
                f"Tests Passed: {getattr(tests, 'passed', 0)}",
                f"Tests Failed: {getattr(tests, 'failed', 0)}",
            ]
        )
