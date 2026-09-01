"""
=========================================================
Patch Builder
=========================================================
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from .models import (
    Patch,
    PatchFile,
)


class PatchBuilder:
    """
    Builds Patch model instances.

    The builder only constructs patch metadata and affected
    file records. It does not persist or execute patches.
    """

    # ========================================================
    # Patch Creation
    # ========================================================

    def create(
        self,
        title: str,
        description: str,
    ) -> Patch:
        return Patch(
            id=uuid.uuid4().hex,
            title=title,
            description=description,
            created_at=datetime.now(
                UTC,
            ),
        )

    # ========================================================
    # File Registration
    # ========================================================

    def add_created(
        self,
        patch: Patch,
        path: str,
        additions: int,
    ) -> None:
        patch.add_file(
            PatchFile(
                path=path,
                action="CREATE",
                additions=additions,
            )
        )

    def add_modified(
        self,
        patch: Patch,
        path: str,
        additions: int,
        deletions: int,
    ) -> None:
        patch.add_file(
            PatchFile(
                path=path,
                action="MODIFY",
                additions=additions,
                deletions=deletions,
            )
        )

    def add_deleted(
        self,
        patch: Patch,
        path: str,
    ) -> None:
        patch.add_file(
            PatchFile(
                path=path,
                action="DELETE",
            )
        )

    # ========================================================
    # Utilities
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        return f"{self.__class__.__name__}()"

    def __str__(
        self,
    ) -> str:
        return "QUANT AI Architect Patch Builder"
