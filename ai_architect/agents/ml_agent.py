from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent


class MLAgent(BaseAgent):
    name = "Machine Learning Agent"

    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        project_path = Path(project)

        models: list[str] = []

        for file in project_path.rglob("*.py"):
            source = file.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            if (
                "lightgbm" in source.lower()
                or "xgboost" in source.lower()
                or "catboost" in source.lower()
                or "sklearn" in source.lower()
            ):
                models.append(str(file))

        return {
            "ml_modules": len(models),
            "files": models,
        }
