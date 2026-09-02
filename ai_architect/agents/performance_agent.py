"""
=========================================================
Performance Agent
=========================================================
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base_agent import BaseAgent
from .scope import archivos_py

REGLAS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "iterrows",
        re.compile(r"\.iterrows\s*\("),
        "iterrows recorre el DataFrame fila a fila",
    ),
    (
        "range_len",
        re.compile(r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\("),
        "range(len(...)) en vez de enumerate",
    ),
    (
        "concat_en_bucle",
        re.compile(r"^\s*\w+\s*\+=\s*['\"]"),
        "concatenar cadenas en bucle: usa una lista y join",
    ),
)


class PerformanceAgent(BaseAgent):
    name = "Performance Agent"

    def run(
        self,
        context,
    ):
        return self.review(
            context,
        )

    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []

        for file in archivos_py(Path(project)):
            try:
                source = file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

            except Exception:
                continue

            for numero, linea in enumerate(source.splitlines(), start=1):
                for regla, patron, detalle in REGLAS:
                    if patron.search(linea):
                        findings.append(
                            {
                                "file": str(file),
                                "line": numero,
                                "type": regla,
                                "issue": detalle,
                            }
                        )

        return {
            "agent": self.name,
            "findings": findings,
            "total": len(findings),
            "status": "OK",
        }

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "rendimiento",
            "Pandas Iteration Detection",
            "Index Loop Detection",
            "String Concatenation Detection",
        ]
