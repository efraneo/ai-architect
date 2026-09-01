"""
=========================================================
Import Analyzer
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .python_analyzer import (
    PythonAnalyzer,
)


class ImportAnalyzer:
    def __init__(self):

        self.analyzer = PythonAnalyzer()

    def imports(
        self,
        file: str | Path,
    ) -> list[str]:

        analysis = self.analyzer.analyze(file)

        result = []

        for item in analysis.imports:
            result.append(item.module)

        return sorted(set(result))

    def depends_on(
        self,
        file: str | Path,
        module: str,
    ) -> bool:

        return module in self.imports(file)
