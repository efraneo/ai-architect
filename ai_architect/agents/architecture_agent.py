from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent


class ArchitectureAgent(BaseAgent):
    name = "Architecture Agent"

    MAX_FILE_LINES = 600
    MAX_DEPTH = 6

    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        project_path = Path(project)

        python_files = list(
            project_path.rglob("*.py"),
        )

        oversized: list[str] = []
        deep_modules: list[str] = []
        empty_files: list[str] = []

        total_lines = 0

        for file in python_files:
            lines = sum(
                1
                for _ in file.open(
                    encoding="utf-8",
                    errors="ignore",
                )
            )

            total_lines += lines

            if lines == 0:
                empty_files.append(str(file))

            if lines > self.MAX_FILE_LINES:
                oversized.append(str(file))

            depth = len(file.relative_to(project_path).parts)

            if depth > self.MAX_DEPTH:
                deep_modules.append(str(file))

        average = total_lines / len(python_files) if python_files else 0

        return {
            "python_files": len(python_files),
            "total_lines": total_lines,
            "average_lines": round(
                average,
                2,
            ),
            "oversized_files": oversized,
            "deep_modules": deep_modules,
            "empty_files": empty_files,
            "status": "OK",
        }

    def run(
        self,
        context,
    ):
        return self.review(context)
