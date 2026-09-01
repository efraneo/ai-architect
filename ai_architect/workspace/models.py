"""
=========================================================
Workspace Models
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class WorkspaceFile:

    path: str

    extension: str

    language: str

    sha256: str

    size: int

    modified: float

    imports: list[str] = field(default_factory=list)

    classes: list[str] = field(default_factory=list)

    functions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkspaceSnapshot:

    root: str

    created_at: datetime

    files: list[WorkspaceFile] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def total_size(self) -> int:
        return sum(file.size for file in self.files)
