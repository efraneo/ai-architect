"""
=========================================================
Trading Architect Agent
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .base_agent import BaseAgent


class TradingArchitectAgent(BaseAgent):
    name = "Trading Architect"

    MODULES = (
        "strateg",
        "indicator",
        "smart_money",
        "risk",
        "execution",
        "portfolio",
        "backtest",
    )

    def review(
        self,
        project: str,
    ) -> dict:

        score = 100

        modules = {}

        for module in self.MODULES:
            modules[module] = False

        for file in Path(project).rglob("*.py"):
            path = str(file).lower()

            for module in self.MODULES:
                if module in path:
                    modules[module] = True

        missing = [key for key, value in modules.items() if not value]

        score -= len(missing) * 10

        return {
            "architecture_score": max(
                score,
                0,
            ),
            "missing_modules": missing,
            "status": "OK",
        }
