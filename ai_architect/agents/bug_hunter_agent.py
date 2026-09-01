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

            for numero, detalle in self._silenciosos(source):
                findings.append(
                    {
                        "file": str(file),
                        "line": numero,
                        "type": "silent_except",
                        "issue": detalle,
                    }
                )

            for regla, patron, detalle in REGLAS:
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

    @staticmethod
    def _silenciosos(source: str) -> list[tuple[int, str]]:
        """Los ``except`` cuyo cuerpo es solo ``pass``, sin explicar por qué.

        Se hacía con una expresión regular, y **no funcionaba como decía**:
        ``\\s*`` traga los saltos de línea, así que un comentario de una sola
        línea entre el ``except`` y el ``pass`` seguía casando. La vía de
        escape parecía existir y no existía.

        Aquí se lee por líneas, que es lo que se puede razonar: un comentario
        encima del ``pass`` es una decisión explicada —la misma vía de escape
        que da cualquier linter— y el motivo queda escrito donde se lee.
        """
        encontrados: list[tuple[int, str]] = []

        lineas = source.splitlines()

        for indice, linea in enumerate(lineas):
            if not re.match(r"^\s*except\b[^:]*:\s*$", linea):
                continue

            sangria = len(linea) - len(linea.lstrip())

            explicado = False

            for siguiente in lineas[indice + 1 :]:
                desnuda = siguiente.strip()

                if not desnuda:
                    continue

                if len(siguiente) - len(siguiente.lstrip()) <= sangria:
                    break  # el bloque terminó sin un `pass` solitario

                if desnuda.startswith("#"):
                    explicado = True
                    continue

                if desnuda == "pass" and not explicado:
                    encontrados.append(
                        (
                            indice + 1,
                            "except que solo hace pass: "
                            "el error desaparece sin rastro",
                        )
                    )

                break

        return encontrados

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "Bare Except Detection",
            "Silent Exception Detection",
            "Pending Marker Detection",
            "Mutable Default Detection",
        ]
