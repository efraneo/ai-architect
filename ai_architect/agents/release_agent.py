from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent


class ReleaseAgent(BaseAgent):
    name = "Release Agent"

    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        project_path = Path(project)

        return {
            "version_file": (project_path / "VERSION").exists(),
            "changelog": (project_path / "CHANGELOG.md").exists(),
            "license": (project_path / "LICENSE").exists(),
            "release_ready": False,
            "next_step": "Execute all tests before release.",
        }
