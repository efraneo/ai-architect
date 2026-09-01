"""
=========================================================
Patch Applier

Safe Patch Application
=========================================================
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class PatchApplier:
    """
    Applies unified diff patches to the repository.

    This class is intentionally independent from the
    LLM. It only knows how to safely apply patches.
    """

    def __init__(
        self,
        repository: str,
    ) -> None:

        self.repository = Path(repository).resolve()

    def apply(
        self,
        patch_file: str | Path,
    ) -> bool:

        patch = Path(patch_file)

        if not patch.exists():
            return False

        result = self._run(
            "git",
            "apply",
            "--whitespace=fix",
            str(patch),
        )

        return result.returncode == 0

    def check(
        self,
        patch_file: str | Path,
    ) -> bool:

        patch = Path(patch_file)

        if not patch.exists():
            return False

        result = self._run(
            "git",
            "apply",
            "--check",
            str(patch),
        )

        return result.returncode == 0

    def reverse(
        self,
        patch_file: str | Path,
    ) -> bool:

        patch = Path(patch_file)

        if not patch.exists():
            return False

        result = self._run(
            "git",
            "apply",
            "-R",
            str(patch),
        )

        return result.returncode == 0

    def create_patch(
        self,
        output: str | Path,
    ) -> bool:

        result = self._run(
            "git",
            "diff",
        )

        if result.returncode != 0:
            return False

        Path(output).write_text(
            result.stdout,
            encoding="utf-8",
        )

        return True

    def has_changes(
        self,
    ) -> bool:

        result = self._run(
            "git",
            "diff",
            "--quiet",
        )

        return result.returncode == 1

    def _run(
        self,
        *command: str,
    ) -> subprocess.CompletedProcess:

        return subprocess.run(
            command,
            cwd=self.repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
