from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .base_agent import BaseAgent
from .scope import todo


class ProjectMetricsAgent(BaseAgent):
    name = "Project Metrics Agent"

    SOURCE_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".java",
        ".kt",
        ".go",
        ".rs",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".cs",
        ".php",
        ".rb",
    }

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

        # Binaries are not excluded here: an image is part of the project
        # and counts towards its size. What is excluded is what does not
        # belong to it -- ``.venv``, ``node_modules``, caches.
        files = todo(project_path)

        total_files = 0
        total_dirs = 0
        total_lines = 0
        total_size = 0

        languages: Counter[str] = Counter()

        python_files = 0

        # Los archivos que no se pudieron leer. Antes se descartaban en
        # silencio con un `except: pass`, así que el tamaño y las líneas
        # salían por debajo de lo real y nadie tenía forma de saberlo.
        ilegibles = 0

        for item in files:
            if item.is_dir():
                total_dirs += 1
                continue

            total_files += 1

            try:
                total_size += item.stat().st_size
            except OSError:
                ilegibles += 1

            suffix = item.suffix.lower()

            if suffix in self.SOURCE_EXTENSIONS:
                languages[suffix] += 1

            if suffix == ".py":
                python_files += 1

                try:
                    with item.open(
                        encoding="utf-8",
                        errors="ignore",
                    ) as file:
                        total_lines += sum(1 for _ in file)

                except OSError:
                    ilegibles += 1

        average = total_lines / python_files if python_files else 0

        largest = self._largest_files(
            project_path,
        )

        informe: dict[str, Any] = {
            "agent": self.name,
            "files": total_files,
            "directories": total_dirs,
            "python_files": python_files,
            "lines_of_code": total_lines,
            "average_python_file": round(
                average,
                2,
            ),
            "repository_size_mb": round(
                total_size / (1024 * 1024),
                2,
            ),
            "languages": dict(languages),
            "unreadable": ilegibles,
            "largest_files": largest,
            "status": "OK",
        }

        if ilegibles:
            informe["findings"] = [
                {
                    "type": "ilegible",
                    "issue": (
                        f"{ilegibles} archivos no se pudieron leer: "
                        "las métricas salen por debajo de lo real"
                    ),
                }
            ]

        return informe

    def _largest_files(
        self,
        project: Path,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []

        for item in todo(project):
            if not item.is_file():
                continue

            try:
                files.append(
                    {
                        "file": str(item.relative_to(project)),
                        "size": item.stat().st_size,
                    }
                )

            except Exception:
                continue

        files.sort(
            key=lambda item: int(item["size"]),
            reverse=True,
        )

        return files[:limit]

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "metricas",
            "Repository Metrics",
            "Language Distribution",
            "Repository Size",
            "Lines of Code",
            "Largest Files",
            "Project Statistics",
        ]
