"""
DevOps Agent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class DevOpsAgent:
    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        root = Path(project)

        return {
            "docker": (root / "Dockerfile").exists(),
            "github_actions": (root / ".github").exists(),
            "pyproject": (root / "pyproject.toml").exists(),
        }
