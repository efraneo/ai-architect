"""
=========================================================
ChangeLog Models
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ChangeType(StrEnum):
    CREATE = "CREATE"

    UPDATE = "UPDATE"

    DELETE = "DELETE"

    REFACTOR = "REFACTOR"

    FIX = "FIX"


@dataclass(slots=True)
class ChangeItem:
    file: str

    change_type: ChangeType

    summary: str

    additions: int = 0

    deletions: int = 0


@dataclass(slots=True)
class ChangeLogEntry:
    version: str

    author: str

    created_at: datetime = field(default_factory=datetime.utcnow)

    changes: list[ChangeItem] = field(default_factory=list)

    def add(
        self,
        item: ChangeItem,
    ) -> None:

        self.changes.append(item)

    @property
    def total_changes(
        self,
    ) -> int:

        return len(self.changes)
