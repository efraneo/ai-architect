"""
=========================================================
Git Manager

Unified Git Facade
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.git.commit_manager import (
    CommitManager,
)
from ai_architect.git.diff_manager import (
    DiffManager,
)
from ai_architect.git.patch_applier import (
    PatchApplier,
)


class GitManager:
    """
    Unified Git interface used by the AI Architect.

    All Git operations should be accessed through this
    class instead of interacting directly with Git.
    """

    def __init__(
        self,
        repository: str | Path,
    ) -> None:

        self.repository = Path(repository).resolve()

        self.committer = CommitManager(
            str(self.repository),
        )

        self.diff = DiffManager(
            str(self.repository),
        )

        self.patch = PatchApplier(
            str(self.repository),
        )

    # --------------------------------------------------
    # Repository
    # --------------------------------------------------

    def is_repository(self) -> bool:

        return (self.repository / ".git").exists()

    # --------------------------------------------------
    # Commit
    # --------------------------------------------------

    def commit(
        self,
        message: str,
    ) -> bool:

        return self.committer.commit(
            message,
        )

    def stage_all(
        self,
    ) -> bool:

        return self.committer.stage_all()

    def rollback(
        self,
    ) -> bool:

        return self.committer.rollback_last_commit()

    def discard_changes(
        self,
    ) -> bool:

        return self.committer.discard_changes()

    # --------------------------------------------------
    # Diff
    # --------------------------------------------------

    def diff_text(
        self,
    ) -> str:

        return self.diff.diff()

    def changed_files(
        self,
    ) -> list[str]:

        return self.diff.changed_files()

    def staged_files(
        self,
    ) -> list[str]:

        return self.diff.staged_files()

    def statistics(
        self,
    ) -> dict:

        return self.diff.statistics()

    def has_changes(
        self,
    ) -> bool:

        return self.diff.has_changes()

    # --------------------------------------------------
    # Patch
    # --------------------------------------------------

    def apply_patch(
        self,
        patch: str,
    ) -> bool:

        return self.patch.apply(
            patch,
        )

    def validate_patch(
        self,
        patch: str,
    ) -> bool:

        return self.patch.check(
            patch,
        )

    def reverse_patch(
        self,
        patch: str,
    ) -> bool:

        return self.patch.reverse(
            patch,
        )

    def export_patch(
        self,
        filename: str,
    ) -> bool:

        return self.patch.create_patch(
            filename,
        )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    def summary(
        self,
    ) -> dict:

        return {
            "repository": str(self.repository),
            "git": self.is_repository(),
            "changes": self.has_changes(),
            "changed_files": self.changed_files(),
            "statistics": self.statistics(),
        }
