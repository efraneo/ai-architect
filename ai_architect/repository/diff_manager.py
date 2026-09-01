"""
=========================================================
Diff Manager
=========================================================
"""

from __future__ import annotations

import subprocess

from .git_manager import GitManager


class DiffManager:
    def __init__(
        self,
        git: GitManager,
    ) -> None:

        self.git = git

    def _run(
        self,
        *args: str,
    ) -> str:

        result = subprocess.run(
            ["git", *args],
            cwd=self.git.repository,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout

    def working_tree(self) -> str:

        return self._run("diff")

    def staged(self) -> str:

        return self._run(
            "diff",
            "--cached",
        )

    def commit(
        self,
        commit_hash: str,
    ) -> str:

        return self._run(
            "show",
            commit_hash,
        )

    def file(
        self,
        path: str,
    ) -> str:

        return self._run(
            "diff",
            "--",
            path,
        )
