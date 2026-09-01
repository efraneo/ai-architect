"""
=========================================================
Status Manager

``git status --porcelain``, bien leído.
=========================================================

Venía de ``repository/`` y traía dos fallos que aquí no pasan:

- Iba con ``check=True``: fuera de un repositorio git **lanzaba una
  excepción** en vez de decir que no había nada que mirar.
- Clasificaba con ``"A" in code``, ``"M" in code``, ``"D" in code`` en una
  cadena de ``elif``. El código de porcelain son **dos columnas** -- índice y
  árbol de trabajo -- así que un ``AM`` (añadido y luego modificado) contaba
  solo como creado, un ``MM`` solo como modificado, y un renombrado (``R``)
  o un conflicto (``UU``) no contaban en absoluto.

El ``GitAgent``, que sí está conectado, tenía su propia versión igual de
frágil: contaba solo las líneas que empiezan por ``" M"`` o ``"M "``, se
perdía los ``MM`` y los ``AM``, y llamaba a git **dos veces** para el mismo
estado.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ai_architect.git.git_models import GitStatus

TIEMPO_LIMITE = 30


class StatusManager:
    def __init__(
        self,
        repository: str | Path,
    ) -> None:
        self.repository = Path(repository).resolve()

    def status(self) -> GitStatus:
        """El estado del árbol. Fuera de un repositorio, uno vacío."""
        salida = self._git("status", "--porcelain")

        if salida is None:
            return GitStatus()

        estado = GitStatus(branch=self.current_branch())

        for linea in salida.splitlines():
            if len(linea) < 3:
                continue

            self._clasificar(linea, estado)

        return estado

    def is_clean(self) -> bool:
        return self.status().clean

    @staticmethod
    def _clasificar(linea: str, estado: GitStatus) -> None:
        """Reparte una línea de porcelain en la lista que le toca.

        Las dos primeras columnas son el estado en el índice y en el árbol de
        trabajo. Un archivo puede estar en varias a la vez -- ``AM`` es
        añadido *y* modificado -- así que esto no es una cadena de ``elif``.
        """
        indice, arbol = linea[0], linea[1]

        ruta = linea[3:].strip()

        if indice == "?" or arbol == "?":
            estado.untracked.append(ruta)
            return

        if indice == "U" or arbol == "U" or (indice == "A" and arbol == "A"):
            estado.conflicted.append(ruta)
            return

        # Un renombrado llega como "R  viejo -> nuevo": lo que interesa es el
        # nombre nuevo, que es el archivo que existe ahora.
        if indice == "R":
            estado.renamed.append(ruta.split(" -> ")[-1])

        if indice == "A":
            estado.created.append(ruta)

        if indice == "D" or arbol == "D":
            estado.deleted.append(ruta)

        if indice == "M" or arbol == "M":
            estado.modified.append(ruta)

    def current_branch(self) -> str:
        salida = self._git("branch", "--show-current")

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
