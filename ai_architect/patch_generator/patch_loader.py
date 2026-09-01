"""
Patch Loader

Loads Patch objects from disk.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import Patch, PatchFile
from .patch_format import (
    extraer_diff,
    leer_aprobado,
    leer_archivo,
    leer_cabecera,
    valor_de,
)


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

        metadata, files = leer_cabecera(text)

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

        diff = extraer_diff(text)

        # ====================================================
        # Build Patch
        # ====================================================

        approved = leer_aprobado(metadata.get("approved"))

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
    # Format (delegado a patch_format)
    # ========================================================

    @staticmethod
    def _parse_file_entry(
        line: str,
    ) -> PatchFile | None:
        return leer_archivo(line)

    @staticmethod
    def _extract_diff(
        text: str,
    ) -> str:
        return extraer_diff(text)

    @staticmethod
    def _metadata_value(
        line: str,
    ) -> str:
        return valor_de(line)

    @staticmethod
    def _parse_approved(
        value: str | None,
    ) -> bool:
        return leer_aprobado(value)

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
