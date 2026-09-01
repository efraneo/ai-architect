"""
=========================================================
Workspace Manager
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .models import WorkspaceSnapshot
from .workspace_loader import WorkspaceLoader


class WorkspaceManager:

    def __init__(self) -> None:

        self.loader = WorkspaceLoader()

        self._snapshot: WorkspaceSnapshot | None = None

    @property
    def snapshot(self) -> WorkspaceSnapshot | None:
        return self._snapshot

    def open(
        self,
        root: str | Path,
    ) -> WorkspaceSnapshot:

        self._snapshot = self.loader.load(root)

        return self._snapshot

    def reload(self) -> WorkspaceSnapshot:

        if self._snapshot is None:
            raise RuntimeError("Workspace no abierto.")

        return self.open(self._snapshot.root)

    def clear(self) -> None:

        self._snapshot = None

    def total_files(self) -> int:

        if self._snapshot is None:
            return 0

        return self._snapshot.total_files

    def get_file(
        self,
        path: str,
    ):

        if self._snapshot is None:
            return None

        for file in self._snapshot.files:

            if file.path == path:
                return file

        return None
