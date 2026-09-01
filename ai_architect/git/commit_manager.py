"""
=========================================================
Commit Manager

Safe Git Commit Operations
=========================================================
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class CommitManager:
    """
    Handles Git commit operations.

    All git interaction should pass through this class.
    """

    def __init__(
        self,
        repository: str,
    ) -> None:
        self.repository = Path(repository).resolve()

    def commit(
        self,
        message: str,
    ) -> bool:
        if not self.is_git_repository():
            return False

        if not self.stage_all():
            return False

        result = self._run(
            "git",
            "commit",
            "-m",
            message,
        )

        return result.returncode == 0

    def stage_all(self) -> bool:
        result = self._run(
            "git",
            "add",
            "-A",
        )

        return result.returncode == 0

    def stage(
        self,
        *files: str,
    ) -> bool:
        if not files:
            return False

        result = self._run(
            "git",
            "add",
            *files,
        )

        return result.returncode == 0

    def rollback_last_commit(self) -> bool:
        result = self._run(
            "git",
            "reset",
            "--soft",
            "HEAD~1",
        )

        return result.returncode == 0

    def discard_changes(self) -> bool:
        result = self._run(
            "git",
            "restore",
            ".",
        )

        return result.returncode == 0

    def current_commit(self) -> str:
        result = self._run(
            "git",
            "rev-parse",
            "HEAD",
        )

        return str(result.stdout.strip())

    def commit_count(self) -> int:
        result = self._run(
            "git",
            "rev-list",
            "--count",
            "HEAD",
        )

        try:
            return int(result.stdout.strip())
        except ValueError:
            return 0

    def is_git_repository(self) -> bool:
        return (self.repository / ".git").exists()

    def _run(
        self,
        *command: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=self.repository,
            capture_output=True,
            text=True,
            check=False,
        )
