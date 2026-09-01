"""
=========================================================
Repository Manager

Punto único de acceso al módulo Git.
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .branch_manager import BranchManager
from .commit_manager import CommitManager
from .diff_manager import DiffManager
from .git_manager import GitManager
from .status_manager import StatusManager
from .tag_manager import TagManager


class RepositoryManager:
    def __init__(
        self,
        repository: str | Path,
    ) -> None:

        self.git = GitManager(repository)

        self.branches = BranchManager(self.git)

        self.commits = CommitManager(self.git)

        self.diff = DiffManager(self.git)

        self.status = StatusManager(self.git)

        self.tags = TagManager(self.git)

    @property
    def current_branch(
        self,
    ) -> str:

        return self.git.current_branch()

    @property
    def is_clean(
        self,
    ) -> bool:

        return self.status.status().clean
