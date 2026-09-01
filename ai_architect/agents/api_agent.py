"""
=========================================================
API Agent
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .base_agent import BaseAgent


class APIAgent(BaseAgent):
    name = "API Agent"

    FRAMEWORKS = (
        "fastapi",
        "flask",
        "django",
        "aiohttp",
    )

    def review(
        self,
        project: str,
    ) -> dict:

        apis = {}

        for file in Path(project).rglob("*.py"):
            source = file.read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()

            frameworks = [fw for fw in self.FRAMEWORKS if fw in source]

            if frameworks:
                apis[str(file)] = frameworks

        return {
            "api_modules": apis,
            "count": len(apis),
        }
