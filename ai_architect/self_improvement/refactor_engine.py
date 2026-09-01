"""
=========================================================
Refactor Engine
=========================================================
"""

from __future__ import annotations

from pathlib import Path


class RefactorEngine:
    def oversized_files(
        self,
        project: str | Path,
        limit: int = 600,
    ):

        result = []

        project = Path(project)

        for file in project.rglob("*.py"):
            total = sum(1 for _ in file.open(encoding="utf-8"))

            if total > limit:
                result.append(
                    {
                        "file": str(file),
                        "lines": total,
                    }
                )

        return result

    def suggest(
        self,
        file: str,
        total_lines: int,
    ):

        modules = (total_lines // 300) + 1

        return f"Split into {modules} modules."
