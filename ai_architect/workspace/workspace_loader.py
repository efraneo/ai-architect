"""
=========================================================
Workspace Loader

Construye un snapshot completo del proyecto.
=========================================================
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_architect.filesystem.file_hash import FileHash
from ai_architect.filesystem.project_walker import (
    ProjectWalker,
)

from .models import (
    WorkspaceFile,
    WorkspaceSnapshot,
)


LANGUAGE_MAP = {
    ".py": "python",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".txt": "text",
}


class WorkspaceLoader:
    """
    Builds an immutable snapshot of the workspace.

    This class is responsible only for transforming the
    filesystem into WorkspaceFile models.
    """

    def __init__(
        self,
    ) -> None:

        self.hasher = FileHash()

    def load(
        self,
        root: str | Path,
    ) -> WorkspaceSnapshot:

        root = Path(root).resolve()

        snapshot = WorkspaceSnapshot(
            root=str(root),
            created_at=datetime.utcnow(),
        )

        walker = ProjectWalker(
            root=root,
        )

        for project_file in walker.walk():

            extension = project_file.extension

            snapshot.files.append(

                WorkspaceFile(

                    path=str(project_file.path),

                    extension=extension,

                    language=LANGUAGE_MAP.get(
                        extension,
                        "unknown",
                    ),

                    sha256=self.hasher.sha256(
                        project_file.path,
                    ),

                    size=project_file.size_bytes,

                    modified=project_file.path.stat().st_mtime,

                )

            )

        return snapshot
