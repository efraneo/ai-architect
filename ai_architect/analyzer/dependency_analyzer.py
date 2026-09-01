"""
=========================================================
Dependency Analyzer
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.knowledge.dependency_index import (
    DependencyIndex,
)

from .import_analyzer import (
    ImportAnalyzer,
)


class DependencyAnalyzer:
    def __init__(self):

        self.imports = ImportAnalyzer()

        self.index = DependencyIndex()

    def analyze_file(
        self,
        file: str | Path,
    ) -> None:

        modules = self.imports.imports(file)

        for module in modules:
            self.index.add_import(
                str(file),
                module,
            )

    def analyze_project(
        self,
        files: list[str],
    ) -> DependencyIndex:

        self.index.clear()

        for file in files:
            self.analyze_file(file)

        return self.index
