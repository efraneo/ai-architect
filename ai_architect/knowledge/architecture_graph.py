"""
Architecture Graph.
"""

from __future__ import annotations

from pathlib import Path


class ArchitectureGraph:
    def build(
        self,
        project: str,
    ) -> dict[str, int]:
        folders: dict[str, int] = {}
        root = Path(project)

        for directory in root.rglob("*"):
            if directory.is_dir():
                folders[str(directory)] = len(list(directory.glob("*")))

        return folders
