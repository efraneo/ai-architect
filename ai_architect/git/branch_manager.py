"""
=========================================================
Branch Manager

Ramas, sobre el repositorio que se le diga.
=========================================================

Venía de ``autonomous/``, donde llamaba a git **sin ``cwd``**: operaba sobre
el directorio en el que estuviera el proceso, no sobre el repositorio que se
estaba analizando. Al revisar un proyecto ajeno habría creado la rama en el
repositorio equivocado.

Aquí vive con el resto de git, con el repositorio como argumento obligatorio
y el resultado comprobado -- antes iba con ``check=False`` y nadie miraba si
había funcionado.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

TIEMPO_LIMITE = 30


class BranchManager:
    def __init__(
        self,
        repository: str | Path,
    ) -> None:
        self.repository = Path(repository).resolve()

    def current(self) -> str:
        """La rama en la que está el repositorio, o cadena vacía."""
        resultado = self._git("branch", "--show-current")

        return resultado.stdout.strip() if resultado else ""

    def exists(
        self,
        name: str,
    ) -> bool:
        resultado = self._git("rev-parse", "--verify", "--quiet", f"refs/heads/{name}")

        return bool(resultado and resultado.returncode == 0)

    def create(
        self,
        name: str,
    ) -> bool:
        """Crea la rama y se cambia a ella. Devuelve si funcionó.

        Antes no devolvía nada y usaba ``check=False``: si git fallaba -- por
        una rama que ya existía, por ejemplo -- el trabajo seguía adelante
        creyendo que estaba en la rama nueva.
        """
        resultado = self._git("checkout", "-b", name)

        return bool(resultado and resultado.returncode == 0)

    def checkout(
        self,
        name: str,
    ) -> bool:
        resultado = self._git("checkout", name)

        return bool(resultado and resultado.returncode == 0)

    def merge(
        self,
        branch: str,
    ) -> bool:
        """Fusiona ``branch`` en la rama actual. Devuelve si funcionó.

        Un conflicto deja el repositorio a medias y devuelve ``False``: quien
        llame tiene que enterarse, no seguir como si nada.
        """
        resultado = self._git("merge", "--no-edit", branch)

        return bool(resultado and resultado.returncode == 0)

    def _git(
        self,
        *argumentos: str,
    ) -> subprocess.CompletedProcess[str] | None:
        if not (self.repository / ".git").exists():
            return None

        try:
            return subprocess.run(
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
