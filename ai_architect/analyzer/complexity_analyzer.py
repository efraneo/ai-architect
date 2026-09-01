"""
=========================================================
Complexity Analyzer
=========================================================
"""

from __future__ import annotations

import ast
from pathlib import Path

_COMPLEXITY_NODES = (
    ast.If,
    ast.For,
    ast.While,
    ast.Try,
    ast.With,
    ast.BoolOp,
    ast.IfExp,
    ast.Match,
)


class ComplexityAnalyzer:
    def score(
        self,
        file: str | Path,
    ) -> int:

        source = Path(file).read_text(encoding="utf-8")

        tree = ast.parse(source)

        complexity = 1

        for node in ast.walk(tree):
            if isinstance(
                node,
                _COMPLEXITY_NODES,
            ):
                complexity += 1

        return complexity

    def exceeds_limit(
        self,
        file: str | Path,
        limit: int = 10,
    ) -> bool:

        return self.score(file) > limit

    def level(
        self,
        file: str | Path,
    ) -> str:

        score = self.score(file)

        if score <= 5:
            return "LOW"

        if score <= 10:
            return "MEDIUM"

        if score <= 20:
            return "HIGH"

        return "CRITICAL"
