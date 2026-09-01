"""
File Graph.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class FileGraph:
    def build(
        self,
        project: str,
    ) -> dict[str, dict[str, Any]]:
        graph: dict[str, dict[str, Any]] = {}
        root = Path(project)

        for file in root.rglob("*.py"):
            graph[str(file)] = {
                "size": file.stat().st_size,
                "folder": str(file.parent),
            }

        return graph
