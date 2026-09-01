"""
Patch Writer

Persists Patch objects to disk.
"""

from __future__ import annotations

from pathlib import Path

from .models import Patch


class PatchWriter:
    """
    Writes QUANT AI Architect Patch objects to disk.

    The writer preserves:

    - patch metadata
    - approval state
    - file actions
    - additions
    - deletions
    - unified diff content
    - exact trailing newline semantics of the diff
    """

    # ========================================================
    # Public API
    # ========================================================

    def save(
        self,
        patch: Patch,
        directory: str | Path,
    ) -> Path:
        """
        Persist a Patch object.

        Parameters
        ----------
        patch:
            Patch to persist.

        directory:
            Destination directory.

        Returns
        -------
        Path
            Path to the generated patch file.
        """

        target_directory = Path(
            directory,
        )

        target_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = f"{patch.id}.patch"

        path = target_directory / filename

        content = self._serialize(
            patch,
        )

        path.write_text(
            content,
            encoding="utf-8",
        )

        return path

    # ========================================================
    # Serialization
    # ========================================================

    def _serialize(
        self,
        patch: Patch,
    ) -> str:
        lines: list[str] = []

        lines.append(
            f"ID: {patch.id}",
        )

        lines.append(
            f"TITLE: {patch.title}",
        )

        lines.append(
            f"DESCRIPTION: {patch.description}",
        )

        lines.append(
            f"CREATED: {patch.created_at.isoformat()}",
        )

        lines.append(
            f"APPROVED: {str(bool(patch.approved)).lower()}",
        )

        lines.append("")

        # ----------------------------------------------------
        # Files
        # ----------------------------------------------------

        lines.append(
            "FILES",
        )

        lines.append(
            "--------------------------------",
        )

        for patch_file in patch.files:
            lines.append(
                (
                    f"{patch_file.action} "
                    f"{patch_file.path} "
                    f"{patch_file.additions} "
                    f"{patch_file.deletions}"
                )
            )

        lines.append("")

        # ----------------------------------------------------
        # Diff
        # ----------------------------------------------------

        diff = patch.diff

        if not diff:
            return "\n".join(
                lines,
            )

        #
        # The diff must be appended directly rather than being
        # processed with strip(), rstrip(), splitlines(), etc.
        #
        # The separator above already provides the blank line
        # between FILES and the diff.
        #
        prefix = "\n".join(
            lines,
        )

        return (
            prefix
            + "\n"
            + diff
        )

    # ========================================================
    # Utilities
    # ========================================================

    def exists(
        self,
        patch: str | Path,
    ) -> bool:
        return Path(
            patch,
        ).exists()

    def filename(
        self,
        patch: Patch,
    ) -> str:
        return f"{patch.id}.patch"

    # ========================================================
    # Convenience
    # ========================================================

    def __call__(
        self,
        patch: Patch,
        directory: str | Path,
    ) -> Path:
        return self.save(
            patch,
            directory,
        )

    # ========================================================

    def __repr__(
        self,
    ) -> str:
        return f"{self.__class__.__name__}()"

    # ========================================================

    def __str__(
        self,
    ) -> str:
        return "QUANT AI Architect Patch Writer"
