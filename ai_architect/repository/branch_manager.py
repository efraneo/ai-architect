"""
=========================================================
Branch Manager
=========================================================
"""

from __future__ import annotations

from .git_manager import GitManager


class BranchManager:
    def __init__(
        self,
        git: GitManager,
    ) -> None:

        self.git = git

    def exists(
        self,
        name: str,
    ) -> bool:

        return any(branch.name == name for branch in self.git.branches())

    def create(
        self,
        name: str,
        checkout: bool = True,
    ) -> None:

        if self.exists(name):
            return

        self.git.create_branch(name)

        if checkout:
            self.git.checkout(name)

    def switch(
        self,
        name: str,
    ) -> None:

        self.git.checkout(name)

    def current(
        self,
    ) -> str:

        return self.git.current_branch()
