"""
=========================================================
Commit Manager
=========================================================
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .git_manager import GitManager


class CommitManager:
    def __init__(
        self,
        git: GitManager,
    ) -> None:

        self.git = git

    @property
    def repository(self) -> Path:

        return self.git.repository

    def _run(
        self,
        *args: str,
    ) -> str:

        result = subprocess.run(
            ["git", *args],
            cwd=self.repository,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip()

    def stage_all(
        self,
    ) -> None:

        self._run(
            "add",
            ".",
        )

    def stage(
        self,
        *files: str,
    ) -> None:

        self._run(
            "add",
            *files,
        )

    def commit(
        self,
        message: str,
    ) -> None:

        self._run(
            "commit",
            "-m",
            message,
        )

    def last_commit_hash(
        self,
    ) -> str:

        return self._run(
            "rev-parse",
            "HEAD",
        )

    def last_commit_message(
        self,
    ) -> str:

        return self._run(
            "log",
            "-1",
            "--pretty=%B",
        )
