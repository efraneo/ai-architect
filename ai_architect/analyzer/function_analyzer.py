"""
=========================================================
Function Analyzer
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .models import FunctionInfo
from .python_analyzer import PythonAnalyzer


class FunctionAnalyzer:
    def __init__(self) -> None:

        self.python = PythonAnalyzer()

    def functions(
        self,
        file: str | Path,
    ) -> list[FunctionInfo]:

        analysis = self.python.analyze(file)

        return analysis.functions

    def names(
        self,
        file: str | Path,
    ) -> list[str]:

        return sorted(fn.name for fn in self.functions(file))

    def exists(
        self,
        file: str | Path,
        function_name: str,
    ) -> bool:

        return function_name in self.names(file)

    def total(
        self,
        file: str | Path,
    ) -> int:

        return len(self.functions(file))
