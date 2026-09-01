"""
=========================================================
Knowledge Base
=========================================================
"""

from __future__ import annotations

from ai_architect.workspace.models import (
    WorkspaceFile,
)


class KnowledgeBase:
    def __init__(self):

        self._files: dict[
            str,
            WorkspaceFile,
        ] = {}

    def add(
        self,
        file: WorkspaceFile,
    ) -> None:

        self._files[file.path] = file

    def remove(
        self,
        path: str,
    ) -> None:

        self._files.pop(
            path,
            None,
        )

    def clear(self):

        self._files.clear()

    def exists(
        self,
        path: str,
    ) -> bool:

        return path in self._files

    def get(
        self,
        path: str,
    ) -> WorkspaceFile | None:

        return self._files.get(path)

    def all_files(self):

        return list(self._files.values())

    @property
    def total_files(self):

        return len(self._files)
