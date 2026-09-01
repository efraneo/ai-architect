"""
=========================================================
Repository Scanner

Automatic Repository Discovery
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.llm.file_classifier import (
    FileClassifier,
)


class RepositoryScanner:
    """
    Discovers all editable files inside a repository.

    This class becomes the first stage of the automatic
    AI Architect pipeline.
    """

    EXCLUDED_DIRECTORIES = {
        ".git",
        ".idea",
        ".vscode",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "venv",
        ".venv",
        "env",
        "dist",
        "build",
        ".tox",
    }

    SUPPORTED_EXTENSIONS = {
        ".py",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".ini",
        ".cfg",
    }

    def __init__(self):

        self.classifier = FileClassifier()

    def scan(
        self,
        repository: str | Path,
    ) -> list[dict]:

        root = Path(repository).resolve()

        files: list[dict] = []

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if self._is_excluded(path):
                continue

            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            relative = str(path.relative_to(root))

            info = self.classifier.classify(
                relative,
            )

            info["priority"] = self.classifier.importance(
                relative,
            )

            files.append(info)

        files.sort(
            key=lambda item: item["priority"],
            reverse=True,
        )

        return files

    def editable_files(
        self,
        repository: str | Path,
    ) -> list[str]:

        editable: list[str] = []

        for item in self.scan(
            repository,
        ):
            if self.classifier.is_editable(
                item["path"],
            ):
                editable.append(item["path"])

        return editable

    def python_files(
        self,
        repository: str | Path,
    ) -> list[str]:

        return [
            item["path"]
            for item in self.scan(
                repository,
            )
            if item["python"]
        ]

    def summary(
        self,
        repository: str | Path,
    ) -> dict:

        files = self.scan(
            repository,
        )

        return {
            "total": len(files),
            "python": sum(item["python"] for item in files),
            "tests": sum(item["test"] for item in files),
            "configuration": sum(item["configuration"] for item in files),
            "documentation": sum(item["documentation"] for item in files),
        }

    def _is_excluded(
        self,
        path: Path,
    ) -> bool:

        return any(part in self.EXCLUDED_DIRECTORIES for part in path.parts)
