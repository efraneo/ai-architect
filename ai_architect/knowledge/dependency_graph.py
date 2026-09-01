"""
Dependency Graph.
"""

from __future__ import annotations

import ast
from pathlib import Path


class DependencyGraph:
    def build(
        self,
        project: str,
    ) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}
        root = Path(project)

        for file in root.rglob("*.py"):
            imports: list[str] = []

            tree = ast.parse(
                file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            )

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

            graph[str(file)] = sorted(set(imports))

        return graph
