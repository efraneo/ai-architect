"""
Patch Loader

Loads Patch objects from disk.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .models import Patch, PatchFile


class PatchLoader:
    """
    Loads .patch files into Patch models.

    The loader understands the QUANT AI Architect patch
    container format and extracts the embedded Git diff.

    The loader preserves:

    - patch metadata
    - approval state
    - file actions
    - additions
    - deletions
    - exact diff content
    - exact trailing newline semantics
    """

    # ========================================================
    # Public API
    # ========================================================

    def load(
        self,
        file: str | Path,
    ) -> Patch:
        """
        Load a Patch object from disk.
        """

        path = Path(
            file,
        )

        if not path.exists():
            raise FileNotFoundError(
                path,
            )

        text = path.read_text(
            encoding="utf-8",
        )

        patch = self._parse(
            text,
        )

        return patch

    # ========================================================
    # Internal Parser
    # ========================================================

    def _parse(
        self,
        text: str,
    ) -> Patch:

        metadata: dict[str, str] = {}

        files: list[PatchFile] = []

        lines = text.splitlines()

        reading_files = False

        # ====================================================
        # Metadata / FILES
        # ====================================================

        for line in lines:

            # ------------------------------------------------
            # Stop metadata/file parsing once Git diff starts.
            # ------------------------------------------------

            if line.startswith(
                "diff --git ",
            ):
                break

            # ------------------------------------------------
            # Metadata
            # ------------------------------------------------

            if line.startswith(
                "ID:",
            ):
                metadata["id"] = self._metadata_value(
                    line,
                )
                continue

            if line.startswith(
                "TITLE:",
            ):
                metadata["title"] = self._metadata_value(
                    line,
                )
                continue

            if line.startswith(
                "DESCRIPTION:",
            ):
                metadata["description"] = self._metadata_value(
                    line,
                )
                continue

            if line.startswith(
                "CREATED:",
            ):
                metadata["created"] = self._metadata_value(
                    line,
                )
                continue

            if line.startswith(
                "APPROVED:",
            ):
                metadata["approved"] = self._metadata_value(
                    line,
                )
                continue

            # ------------------------------------------------
            # Files section
            # ------------------------------------------------

            if line.strip() == "FILES":
                reading_files = True
                continue

            # ------------------------------------------------
            # Files separator
            # ------------------------------------------------

            if reading_files and line.strip() and set(line.strip()) == {"-"}:
                continue

            # ------------------------------------------------
            # File entries
            # ------------------------------------------------

            if reading_files:

                if not line.strip():
                    reading_files = False
                    continue

                patch_file = self._parse_file_entry(
                    line,
                )

                if patch_file is not None:
                    files.append(
                        patch_file,
                    )

                continue

        # ====================================================
        # Validate metadata
        # ====================================================

        created = metadata.get(
            "created",
        )

        if not created:
            raise ValueError(
                "Patch is missing CREATED metadata.",
            )

        # ====================================================
        # Extract exact Git diff
        # ====================================================

        diff = self._extract_diff(
            text,
        )

        # ====================================================
        # Build Patch
        # ====================================================

        approved = self._parse_approved(
            metadata.get(
                "approved",
            ),
        )

        patch = Patch(
            id=metadata.get(
                "id",
                "",
            ),
            title=metadata.get(
                "title",
                "",
            ),
            description=metadata.get(
                "description",
                "",
            ),
            created_at=datetime.fromisoformat(
                created,
            ),
            approved=approved,
        )

        patch.files.extend(
            files,
        )

        patch.diff = diff

        return patch

    # ========================================================
    # File Parser
    # ========================================================

    @staticmethod
    def _parse_file_entry(
        line: str,
    ) -> PatchFile | None:
        """
        Parse a persisted PatchFile entry.

        Current format:

            MODIFY path/to/file.py 7 3

        Where:

            action
            path
            additions
            deletions

        Legacy entries containing only:

            MODIFY path/to/file.py

        remain supported and default additions/deletions
        to zero.
        """

        parts = line.split()

        if len(parts) < 2:
            return None

        action = parts[0]

        # ----------------------------------------------------
        # Legacy format:
        #
        # ACTION path
        # ----------------------------------------------------

        if len(parts) == 2:
            return PatchFile(
                path=parts[1],
                action=action,
            )

        # ----------------------------------------------------
        # Current format:
        #
        # ACTION path additions deletions
        #
        # The path itself may contain spaces, therefore parse
        # the final two tokens as numeric counters.
        # ----------------------------------------------------

        try:
            additions = int(
                parts[-2],
            )

            deletions = int(
                parts[-1],
            )

        except ValueError:
            #
            # If the final two fields are not counters, treat
            # the complete remainder as the path for backward
            # compatibility.
            #
            return PatchFile(
                path=" ".join(
                    parts[1:],
                ),
                action=action,
            )

        path = " ".join(
            parts[1:-2],
        )

        if not path:
            return None

        return PatchFile(
            path=path,
            action=action,
            additions=additions,
            deletions=deletions,
        )

    # ========================================================
    # Diff Extraction
    # ========================================================

    @staticmethod
    def _extract_diff(
        text: str,
    ) -> str:
        """
        Extract the Git diff without reconstructing it.

        This deliberately avoids splitlines() + join() because
        that process destroys exact trailing newline semantics.

        Therefore:

            diff == original persisted diff

        including:

            diff ending in \\n
            diff ending in \\n\\n
            diff ending in multiple newlines
        """

        match = re.search(
            r"(?m)^diff --git ",
            text,
        )

        if match is None:
            return ""

        return text[match.start() :]

    # ========================================================
    # Metadata Utilities
    # ========================================================

    @staticmethod
    def _metadata_value(
        line: str,
    ) -> str:
        """
        Extract the value after the first ':'.
        """

        if ":" not in line:
            return ""

        return line.split(
            ":",
            1,
        )[1].strip()

    @staticmethod
    def _parse_approved(
        value: str | None,
    ) -> bool:
        """
        Convert persisted approval metadata into a boolean.

        Missing approval metadata is treated as False so that
        legacy patch files cannot become executable merely by
        being loaded.
        """

        if value is None:
            return False

        normalized = value.strip().lower()

        return normalized in {
            "true",
            "1",
            "yes",
            "approved",
        }

    # ========================================================
    # Utilities
    # ========================================================

    def exists(
        self,
        file: str | Path,
    ) -> bool:
        return Path(
            file,
        ).exists()

    # ========================================================

    def load_if_exists(
        self,
        file: str | Path,
    ) -> Patch | None:

        path = Path(
            file,
        )

        if not path.exists():
            return None

        return self.load(
            path,
        )

    # ========================================================

    def metadata(
        self,
        file: str | Path,
    ) -> dict:

        patch = self.load(
            file,
        )

        return {
            "id": patch.id,
            "title": patch.title,
            "description": patch.description,
            "created": patch.created_at,
            "files": patch.total_files,
            "approved": patch.approved,
        }

    # ========================================================

    def summary(
        self,
        file: str | Path,
    ) -> dict:

        return self.metadata(
            file,
        )

    # ========================================================
    # Convenience
    # ========================================================

    def __call__(
        self,
        file: str | Path,
    ) -> Patch:
        """
        Shortcut:

            loader(file)

        Equivalent to:

            loader.load(file)
        """

        return self.load(
            file,
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
        return "QUANT AI Architect Patch Loader"
