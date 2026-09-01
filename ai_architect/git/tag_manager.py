"""
=========================================================
Tag Manager

Etiquetas de versión.
=========================================================

Venía de ``repository/``, y como el resto de aquella capa iba con
``check=True``: borrar una etiqueta que no existe lanzaba una excepción, y
listar las etiquetas fuera de un repositorio también. Aquí cada operación
dice si funcionó.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

TIEMPO_LIMITE = 30


class TagManager:
    def __init__(
        self,
        repository: str | Path,
    ) -> None:
        self.repository = Path(repository).resolve()

    def list(self) -> list[str]:
        """Las etiquetas, ordenadas. Fuera de un repositorio, ninguna."""
        salida = self._git("tag")

        if not salida:
            return []

        return sorted(salida.split())

    def exists(
        self,
        tag: str,
    ) -> bool:
        return tag in self.list()

    def create(
        self,
        tag: str,
        message: str | None = None,
    ) -> bool:
        """Crea la etiqueta. Devuelve si funcionó.

        Antes no devolvía nada: si la etiqueta ya existía, git fallaba y
        quien llamaba seguía creyendo que la había creado.
        """
        if message:
            return self._git("tag", "-a", tag, "-m", message) is not None

        return self._git("tag", tag) is not None

    def delete(
        self,
        tag: str,
    ) -> bool:
        return self._git("tag", "-d", tag) is not None

    def latest(self) -> str:
        """La etiqueta más reciente por historia, no por orden alfabético."""
        salida = self._git("describe", "--tags", "--abbrev=0")

        return salida.strip() if salida else ""

    def _git(
        self,
        *argumentos: str,
    ) -> str | None:
        if not (self.repository / ".git").exists():
            return None

        try:
            resultado = subprocess.run(
                ["git", *argumentos],
                cwd=self.repository,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=TIEMPO_LIMITE,
            )

        except (OSError, subprocess.SubprocessError):
            return None

        return resultado.stdout if resultado.returncode == 0 else None
