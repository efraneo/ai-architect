"""
=========================================================
Duplicate Detector

Detects duplicated files using SHA256 hashes.
=========================================================
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ai_architect.filesystem.file_hash import FileHash
from ai_architect.filesystem.project_walker import (
    ProjectWalker,
)


class DuplicateDetector:
    """
    Detects duplicated files inside a repository.
    """

    def __init__(
        self,
    ) -> None:

        self.hasher = FileHash()

    def duplicates(
        self,
        root: str | Path,
    ) -> dict[str, list[str]]:

        root = Path(root).resolve()

        walker = ProjectWalker(
            root=root,
        )

        hashes: dict[
            str,
            list[str],
        ] = defaultdict(list)

        for project_file in walker.walk():
            digest = self.hasher.sha256(
                project_file.path,
            )

            hashes[digest].append(
                str(
                    project_file.relative_path,
                )
            )

        return {digest: files for digest, files in hashes.items() if len(files) > 1}

    def total_duplicates(
        self,
        root: str | Path,
    ) -> int:

        return len(
            self.duplicates(
                root,
            )
        )
