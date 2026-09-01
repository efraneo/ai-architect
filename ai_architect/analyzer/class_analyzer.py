"""
=========================================================
Class Analyzer
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .models import ClassInfo
from .python_analyzer import PythonAnalyzer


class ClassAnalyzer:
    def __init__(self) -> None:

        self.python = PythonAnalyzer()

    def classes(
        self,
        file: str | Path,
    ) -> list[ClassInfo]:

        analysis = self.python.analyze(file)

        return analysis.classes

    def names(
        self,
        file: str | Path,
    ) -> list[str]:

        return sorted(cls.name for cls in self.classes(file))

    def exists(
        self,
        file: str | Path,
        class_name: str,
    ) -> bool:

        return class_name in self.names(file)

    def methods(
        self,
        file: str | Path,
        class_name: str,
    ) -> list[str]:

        for cls in self.classes(file):
            if cls.name == class_name:
                return sorted(cls.methods)

        return []
