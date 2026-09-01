"""
=========================================================
Database Agent
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .base_agent import BaseAgent


class DatabaseAgent(BaseAgent):
    name = "Database Agent"

    DATABASES = (
        "sqlite",
        "sqlalchemy",
        "postgres",
        "mysql",
        "redis",
    )

    def review(
        self,
        project: str,
    ) -> dict:

        detected = {}

        for file in Path(project).rglob("*.py"):
            source = file.read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()

            found = [db for db in self.DATABASES if db in source]

            if found:
                detected[str(file)] = found

        return {
            "database_files": detected,
            "total": len(detected),
        }
