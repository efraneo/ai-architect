"""
=========================================================
Diff Manager

Git Difference Manager
=========================================================
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class DiffManager:
    """
    Responsible for obtaining git differences.

    This class never modifies the repository.
    """

    def __init__(
        self,
        repository: str,
    ) -> None:

        self.repository = Path(repository).resolve()

    def diff(self) -> str:

        return self._git(
            "diff",
        )

    def staged_diff(self) -> str:

        return self._git(
            "diff",
            "--cached",
        )

    def file_diff(
        self,
        filename: str,
    ) -> str:

        return self._git(
            "diff",
            "--",
            filename,
        )

    def has_changes(self) -> bool:

        return bool(self.diff().strip())

    def changed_files(
        self,
    ) -> list[str]:

        output = self._git(
            "diff",
            "--name-only",
        )

        return [line.strip() for line in output.splitlines() if line.strip()]

    def staged_files(
        self,
    ) -> list[str]:

        output = self._git(
            "diff",
            "--cached",
            "--name-only",
        )

        return [line.strip() for line in output.splitlines() if line.strip()]

    def statistics(
        self,
    ) -> dict:

        output = self._git(
            "diff",
            "--stat",
        )

        return {
            "files": len(self.changed_files()),
            "summary": output,
        }

    def unified_diff(
        self,
        filename: str,
        lines: int = 3,
    ) -> str:

        return self._git(
            "diff",
            f"--unified={lines}",
            "--",
            filename,
        )

    def _git(
        self,
        *args: str,
    ) -> str:

        result = subprocess.run(
            [
                "git",
                *args,
            ],
            cwd=self.repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        return result.stdout
