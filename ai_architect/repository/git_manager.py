"""
=========================================================
Git Manager
=========================================================
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .git_models import (
    GitBranch,
)


class GitManager:
    def __init__(
        self,
        repository: str | Path,
    ) -> None:

        self.repository = Path(repository)

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

    def current_branch(
        self,
    ) -> str:

        return self._run(
            "branch",
            "--show-current",
        )

    def branches(
        self,
    ) -> list[GitBranch]:

        output = self._run("branch")

        branches = []

        for line in output.splitlines():
            current = line.startswith("*")

            name = line.replace(
                "*",
                "",
            ).strip()

            branches.append(
                GitBranch(
                    name=name,
                    current=current,
                )
            )

        return branches

    def checkout(
        self,
        branch: str,
    ) -> None:

        self._run(
            "checkout",
            branch,
        )

    def create_branch(
        self,
        branch: str,
    ) -> None:

        self._run(
            "checkout",
            "-b",
            branch,
        )

    def status(
        self,
    ) -> str:

        return self._run(
            "status",
            "--short",
        )
