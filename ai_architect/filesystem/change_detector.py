"""
=========================================================
QUANT TITAN AI ARCHITECT

Filesystem Change Detector

Detecta archivos nuevos, modificados y eliminados
comparando snapshots.
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class FileState:
    """
    Represents the state of a file at a point in time.
    """

    path: str
    sha256: str
    size: int
    modified: float


@dataclass(slots=True)
class ChangeSet:
    """
    Result of comparing two filesystem snapshots.
    """

    created: list[FileState] = field(default_factory=list)
    modified: list[FileState] = field(default_factory=list)
    deleted: list[FileState] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.created or self.modified or self.deleted)


class ChangeDetector:
    """
    Compares two filesystem states.
    """

    def detect(
        self,
        previous: dict[str, FileState],
        current: dict[str, FileState],
    ) -> ChangeSet:

        result = ChangeSet()

        previous_paths = set(previous.keys())
        current_paths = set(current.keys())

        for path in sorted(current_paths - previous_paths):
            result.created.append(current[path])

        for path in sorted(previous_paths - current_paths):
            result.deleted.append(previous[path])

        for path in sorted(previous_paths & current_paths):
            old = previous[path]
            new = current[path]

            if (
                old.sha256 != new.sha256
                or old.size != new.size
                or old.modified != new.modified
            ):
                result.modified.append(new)

        return result

    @staticmethod
    def build_state(
        path: Path,
        sha256: str,
    ) -> FileState:

        stat = path.stat()

        return FileState(
            path=str(path),
            sha256=sha256,
            size=stat.st_size,
            modified=stat.st_mtime,
        )
