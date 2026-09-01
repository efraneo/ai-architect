"""
=========================================================
Bug Hunter Agent

Smells that hide real bugs.
=========================================================
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base_agent import BaseAgent
from .scope import archivos_py

# It matched substrings on the whole lowercased file, so ``"pass"`` fired on
# "password", "passed" and "passing", and ``"todo"`` on "todos". Every file
# matched every pattern: the report said nothing.
REGLAS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "bare_except",
        re.compile(r"^\s*except\s*:"),
        "except sin tipo: se traga hasta KeyboardInterrupt",
    ),
    (
        "silent_except",
        re.compile(r"^\s*except[^:]*:\s*(#.*)?$\n\s*pass\s*$", re.MULTILINE),
        "except que solo hace pass: el error desaparece sin rastro",
    ),
    (
        "marker",
        re.compile(r"#\s*(TODO|FIXME|XXX|HACK)\b", re.IGNORECASE),
        "marcador pendiente en el código",
    ),
    (
        "mutable_default",
        re.compile(r"def\s+\w+\([^)]*=\s*(\[\]|\{\})"),
        "argumento por defecto mutable: se comparte entre llamadas",
    ),
)


class BugHunterAgent(BaseAgent):
    name = "Bug Hunter Agent"

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

            for regla, patron, detalle in REGLAS:
                if regla == "silent_except":
                    for coincidencia in patron.finditer(source):
                        findings.append(
                            {
                                "file": str(file),
                                "line": source[: coincidencia.start()].count("\n") + 1,
                                "type": regla,
                                "issue": detalle,
                            }
                        )

                    continue

                for numero, linea in enumerate(source.splitlines(), start=1):
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
            "Bare Except Detection",
            "Silent Exception Detection",
            "Pending Marker Detection",
            "Mutable Default Detection",
        ]
