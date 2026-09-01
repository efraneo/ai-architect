"""
=========================================================
Python Analyzer
=========================================================
"""

from __future__ import annotations

import ast
from pathlib import Path

from .models import (
    ClassInfo,
    FunctionInfo,
    ImportInfo,
    PythonAnalysis,
)


class PythonAnalyzer:
    def analyze(
        self,
        file: str | Path,
    ) -> PythonAnalysis:

        path = Path(file)

        source = path.read_text(encoding="utf-8")

        tree = ast.parse(source)

        analysis = PythonAnalysis()

        analysis.total_lines = len(source.splitlines())

        for node in ast.walk(tree):
            if isinstance(
                node,
                ast.Import,
            ):
                for name in node.names:
                    analysis.imports.append(
                        ImportInfo(
                            module=name.name,
                        )
                    )

            elif isinstance(
                node,
                ast.ImportFrom,
            ):
                analysis.imports.append(
                    ImportInfo(
                        module=node.module or "",
                        imported=[item.name for item in node.names],
                    )
                )

            elif isinstance(
                node,
                ast.FunctionDef,
            ):
                analysis.functions.append(
                    FunctionInfo(
                        name=node.name,
                        line=node.lineno,
                        arguments=len(node.args.args),
                        decorators=[ast.unparse(d) for d in node.decorator_list],
                    )
                )

            elif isinstance(
                node,
                ast.ClassDef,
            ):
                methods = []

                for item in node.body:
                    if isinstance(
                        item,
                        ast.FunctionDef,
                    ):
                        methods.append(item.name)

                analysis.classes.append(
                    ClassInfo(
                        name=node.name,
                        line=node.lineno,
                        methods=methods,
                        bases=[ast.unparse(base) for base in node.bases],
                    )
                )

        analysis.complexity = len(analysis.classes) + len(analysis.functions)

        return analysis
