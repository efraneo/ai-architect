from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent


class TradingAgent(BaseAgent):
    name = "Trading Agent"

    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        project_path = Path(project)

        engines: list[str] = []

        for file in project_path.rglob("*.py"):
            name = file.name.lower()

            if (
                "strategy" in name
                or "indicator" in name
                or "risk" in name
                or "smart_money" in str(file)
            ):
                engines.append(str(file))

        return {
            "engines": len(engines),
            "files": engines,
            "status": "OK",
        }
