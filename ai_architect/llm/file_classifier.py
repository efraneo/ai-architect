"""
=========================================================
File Classifier

Repository File Classification
=========================================================
"""

from __future__ import annotations

from pathlib import Path


class FileClassifier:
    """
    Classifies repository files.

    This information is later used by the planner,
    decision engine and context selector.
    """

    TEST_KEYWORDS = (
        "test",
        "tests",
        "pytest",
    )

    CONFIG_FILES = {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "requirements-dev.txt",
        ".env",
        ".gitignore",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "Makefile",
    }

    DOCUMENTATION = {
        ".md",
        ".rst",
    }

    def classify(
        self,
        filename: str | Path,
    ) -> dict:

        path = Path(filename)

        suffix = path.suffix.lower()

        name = path.name

        result = {
            "path": str(path),
            "name": name,
            "extension": suffix,
            "exists": path.exists(),
            "python": suffix == ".py",
            "test": False,
            "configuration": False,
            "documentation": False,
            "package": False,
            "core": False,
            "generated": False,
        }

        lower = str(path).lower()

        if any(token in lower for token in self.TEST_KEYWORDS):
            result["test"] = True

        if name in self.CONFIG_FILES:
            result["configuration"] = True

        if suffix in self.DOCUMENTATION:
            result["documentation"] = True

        if name == "__init__.py":
            result["package"] = True

        if "ai_architect" in lower:
            result["core"] = True

        if "__pycache__" in lower:
            result["generated"] = True

        if lower.endswith(".pyc"):
            result["generated"] = True

        return result

    def importance(
        self,
        filename: str | Path,
    ) -> int:

        info = self.classify(
            filename,
        )

        score = 0

        if info["core"]:
            score += 100

        if info["python"]:
            score += 50

        if info["configuration"]:
            score += 30

        if info["test"]:
            score += 20

        if info["documentation"]:
            score += 5

        if info["generated"]:
            score -= 100

        return score

    def is_editable(
        self,
        filename: str | Path,
    ) -> bool:

        info = self.classify(
            filename,
        )

        if info["generated"]:
            return False

        if info["documentation"]:
            return False

        return True
