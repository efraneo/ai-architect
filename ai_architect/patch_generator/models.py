"""
=========================================================
Patch Generator Models
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class PatchFile:
    path: str
    action: str
    additions: int = 0
    deletions: int = 0


@dataclass(slots=True)
class Patch:
    id: str
    title: str
    description: str
    created_at: datetime

    files: list[PatchFile] = field(
        default_factory=list,
    )

    diff: str = ""

    approved: bool = False

    def add_file(
        self,
        file: PatchFile,
    ) -> None:
        self.files.append(
            file,
        )

    @property
    def total_files(
        self,
    ) -> int:
        return len(
            self.files,
        )

    @property
    def total_additions(
        self,
    ) -> int:
        return sum(item.additions for item in self.files)

    @property
    def total_deletions(
        self,
    ) -> int:
        return sum(item.deletions for item in self.files)

    @property
    def has_diff(
        self,
    ) -> bool:
        return bool(
            self.diff.strip(),
        )

    @property
    def is_valid(
        self,
    ) -> bool:
        return (
            bool(self.id)
            and bool(self.title.strip())
            and bool(self.description.strip())
            and bool(self.created_at)
            and bool(self.files)
            and self.has_diff
        )
