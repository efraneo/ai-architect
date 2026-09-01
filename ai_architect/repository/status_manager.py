"""
=========================================================
Repository Status Manager
=========================================================
"""

from __future__ import annotations

import subprocess

from .git_manager import GitManager
from .git_models import GitStatus


class StatusManager:
    def __init__(
        self,
        git: GitManager,
    ) -> None:

        self.git = git

    def status(
        self,
    ) -> GitStatus:

        result = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
            ],
            cwd=self.git.repository,
            capture_output=True,
            text=True,
            check=True,
        )

        modified = []
        created = []
        deleted = []
        untracked = []

        for line in result.stdout.splitlines():
            code = line[:2]

            file = line[3:]

            if code == "??":
                untracked.append(file)

            elif "A" in code:
                created.append(file)

            elif "M" in code:
                modified.append(file)

            elif "D" in code:
                deleted.append(file)

        return GitStatus(
            branch=self.git.current_branch(),
            modified=sorted(modified),
            created=sorted(created),
            deleted=sorted(deleted),
            untracked=sorted(untracked),
            clean=not (modified or created or deleted or untracked),
        )
