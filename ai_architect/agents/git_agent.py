from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .base_agent import BaseAgent


class GitAgent(BaseAgent):
    name = "Git Agent"

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

        if not (project_path / ".git").exists():
            return {
                "agent": self.name,
                "git": False,
                "status": "NOT_A_GIT_REPOSITORY",
            }

        return {
            "agent": self.name,
            "git": True,
            "branch": self._branch(project_path),
            "status": self._status(project_path),
            "modified": self._modified(project_path),
            "untracked": self._untracked(project_path),
            "ahead": self._ahead(project_path),
            "behind": self._behind(project_path),
            "last_commit": self._last_commit(project_path),
            "recent_commits": self._recent_commits(project_path),
        }

    def _git(
        self,
        project: Path,
        *args: str,
    ) -> str:
        try:
            result = subprocess.run(
                [
                    "git",
                    *args,
                ],
                cwd=project,
                capture_output=True,
                text=True,
                check=True,
            )

            return result.stdout.strip()

        except Exception:
            return ""

    def _branch(
        self,
        project: Path,
    ) -> str:
        return self._git(
            project,
            "branch",
            "--show-current",
        )

    def _status(
        self,
        project: Path,
    ) -> str:
        return self._git(
            project,
            "status",
            "--short",
        )

    def _modified(
        self,
        project: Path,
    ) -> int:
        return len(
            [
                line
                for line in self._status(project).splitlines()
                if line.startswith(" M") or line.startswith("M ")
            ]
        )

    def _untracked(
        self,
        project: Path,
    ) -> int:
        return len(
            [
                line
                for line in self._status(project).splitlines()
                if line.startswith("??")
            ]
        )

    def _ahead(
        self,
        project: Path,
    ) -> int:
        output = self._git(
            project,
            "rev-list",
            "--left-right",
            "--count",
            "@{upstream}...HEAD",
        )

        if not output:
            return 0

        return int(output.split()[1])

    def _behind(
        self,
        project: Path,
    ) -> int:
        output = self._git(
            project,
            "rev-list",
            "--left-right",
            "--count",
            "@{upstream}...HEAD",
        )

        if not output:
            return 0

        return int(output.split()[0])

    def _last_commit(
        self,
        project: Path,
    ) -> str:
        return self._git(
            project,
            "log",
            "-1",
            "--pretty=%h %s",
        )

    def _recent_commits(
        self,
        project: Path,
        count: int = 5,
    ) -> list[str]:
        output = self._git(
            project,
            "log",
            f"-{count}",
            "--pretty=%h %s",
        )

        return output.splitlines() if output else []

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "Branch Detection",
            "Repository Status",
            "Modified Files",
            "Untracked Files",
            "Commit History",
            "Ahead/Behind Analysis",
        ]
