"""
=========================================================
Tag Manager
=========================================================
"""

from __future__ import annotations

import subprocess

from .git_manager import GitManager


class TagManager:
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

        return result.stdout.strip()

    def list(self) -> list[str]:

        output = self._run("tag")

        if not output:
            return []

        return sorted(output.splitlines())

    def create(
        self,
        tag: str,
        message: str | None = None,
    ) -> None:

        if message:
            self._run(
                "tag",
                "-a",
                tag,
                "-m",
                message,
            )

        else:
            self._run(
                "tag",
                tag,
            )

    def delete(
        self,
        tag: str,
    ) -> None:

        self._run(
            "tag",
            "-d",
            tag,
        )
