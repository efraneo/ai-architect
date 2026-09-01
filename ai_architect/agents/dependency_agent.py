from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent


class DependencyAgent(BaseAgent):
    name = "Dependency Agent"

    DEPENDENCY_FILES = [
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "Pipfile",
        "Pipfile.lock",
        "setup.py",
        "setup.cfg",
    ]

    def run(
        self,
        context,
    ):
        return self.review(
            context,
        )

    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        project_path = Path(project)

        dependencies: list[str] = []
        dependency_files: list[str] = []

        for filename in self.DEPENDENCY_FILES:
            file = project_path / filename

            if not file.exists():
                continue

            dependency_files.append(str(file))

            try:
                lines = file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).splitlines()

            except Exception:
                continue

            for line in lines:
                line = line.strip()

                if not line or line.startswith("#") or line.startswith("["):
                    continue

                dependencies.append(line)

        return {
            "agent": self.name,
            "dependency_files": dependency_files,
            "dependency_count": len(dependencies),
            "dependencies": sorted(set(dependencies)),
            "status": "OK" if dependency_files else "NOT_FOUND",
        }

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "Requirements Detection",
            "Poetry Detection",
            "Pipenv Detection",
            "Dependency Inventory",
            "Dependency Statistics",
        ]
