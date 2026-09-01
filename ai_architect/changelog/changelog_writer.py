"""
=========================================================
Markdown ChangeLog Writer

Escribe el CHANGELOG sin borrar lo que ya había.
=========================================================

La versión anterior hacía ``file.write_text(...)`` con **una sola entrada**:
llamarla dos veces dejaba solo la última. Un changelog que olvida lo
anterior no es un changelog, y era el fallo que impedía usar esto para lo
único que sirve — acumular versiones.
"""

from __future__ import annotations

from pathlib import Path

from .models import (
    ChangeLogEntry,
)

CABECERA = "# ChangeLog"


class ChangeLogWriter:
    def render(
        self,
        entry: ChangeLogEntry,
    ) -> str:
        """El bloque de una versión, sin cabecera ni nada de alrededor."""
        lineas = [
            f"## {entry.version}",
            "",
            f"Autor: {entry.author}",
            f"Fecha: {entry.created_at}",
            "",
        ]

        if not entry.changes:
            lineas.append("Sin cambios registrados.")
            lineas.append("")

        for item in entry.changes:
            movimiento = ""

            if item.additions or item.deletions:
                movimiento = f" (+{item.additions}/-{item.deletions})"

            lineas.append(f"- **[{item.change_type}]** `{item.file}`{movimiento}")

            if item.summary:
                lineas.append(f"  {item.summary}")

            lineas.append("")

        return "\n".join(lineas)

    def write(
        self,
        entry: ChangeLogEntry,
        file: str | Path,
    ) -> None:
        """Añade la entrada **arriba**, conservando las versiones anteriores.

        Lo nuevo va primero porque es lo que se lee: quien abre un CHANGELOG
        quiere saber qué cambió en la última versión, no en la primera.
        """
        destino = Path(file)

        destino.parent.mkdir(parents=True, exist_ok=True)

        anterior = ""

        if destino.is_file():
            try:
                anterior = destino.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                anterior = ""

        destino.write_text(
            self._componer(self.render(entry), anterior),
            encoding="utf-8",
        )

    @staticmethod
    def _componer(bloque: str, anterior: str) -> str:
        """Mete el bloque nuevo justo debajo de la cabecera."""
        cuerpo = anterior.strip()

        if cuerpo.startswith(CABECERA):
            cuerpo = cuerpo[len(CABECERA) :].strip()

        partes = [CABECERA, "", bloque.strip()]

        if cuerpo:
            partes.extend(["", cuerpo])

        return "\n".join(partes) + "\n"
