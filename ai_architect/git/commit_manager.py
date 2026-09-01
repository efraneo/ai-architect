"""
=========================================================
Commit Manager

Safe Git Commit Operations
=========================================================
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _entero(valor: str) -> int:
    """``--numstat`` pone ``-`` en los binarios, donde no hay líneas que contar."""
    try:
        return int(valor.strip())
    except ValueError:
        return 0


class CommitManager:
    """
    Handles Git commit operations.

    All git interaction should pass through this class.
    """

    def __init__(
        self,
        repository: str,
    ) -> None:
        self.repository = Path(repository).resolve()

    def commit(
        self,
        message: str,
    ) -> bool:
        if not self.is_git_repository():
            return False

        if not self.stage_all():
            return False

        result = self._run(
            "git",
            "commit",
            "-m",
            message,
        )

        return result.returncode == 0

    def stage_all(self) -> bool:
        result = self._run(
            "git",
            "add",
            "-A",
        )

        return result.returncode == 0

    def stage(
        self,
        *files: str,
    ) -> bool:
        if not files:
            return False

        result = self._run(
            "git",
            "add",
            *files,
        )

        return result.returncode == 0

    def rollback_last_commit(self) -> bool:
        result = self._run(
            "git",
            "reset",
            "--soft",
            "HEAD~1",
        )

        return result.returncode == 0

    def discard_changes(self) -> bool:
        result = self._run(
            "git",
            "restore",
            ".",
        )

        return result.returncode == 0

    def current_commit(self) -> str:
        result = self._run(
            "git",
            "rev-parse",
            "HEAD",
        )

        return str(result.stdout.strip())

    def commit_count(self) -> int:
        result = self._run(
            "git",
            "rev-list",
            "--count",
            "HEAD",
        )

        try:
            return int(result.stdout.strip())
        except ValueError:
            return 0

    def history(
        self,
        since: str = "",
        limit: int = 200,
    ) -> list[dict[str, object]]:
        """Los commits desde una referencia, con qué tocó cada uno.

        ``since`` suele ser la última etiqueta: así el changelog cubre lo que
        va de la versión anterior a hoy. Vacío, devuelve todo el historial
        hasta ``limit``.

        Cada commit trae ``hash``, ``subject`` y la lista de ``files`` con
        sus líneas añadidas y borradas.
        """
        if not self.is_git_repository():
            return []

        rango = f"{since}..HEAD" if since else "HEAD"

        result = self._run(
            "git",
            "log",
            rango,
            f"-{limit}",
            "--numstat",
            "--pretty=format:%H %s",
        )

        if result.returncode != 0:
            return []

        return self._parse_history(result.stdout)

    @staticmethod
    def _parse_history(salida: str) -> list[dict[str, object]]:
        """Separa los commits de sus estadísticas por archivo.

        ``--numstat`` intercala dos formas de línea: la del commit
        (``hash asunto``) y las de archivo (``añadidas\tborradas\truta``).
        Se distinguen por el tabulador.
        """
        commits: list[dict[str, object]] = []

        for linea in salida.splitlines():
            if not linea.strip():
                continue

            if "\t" in linea:
                if not commits:
                    continue

                añadidas, borradas, ruta = (linea.split("\t") + ["", "", ""])[:3]

                archivos = commits[-1]["files"]

                if isinstance(archivos, list):
                    archivos.append(
                        {
                            "path": ruta.strip(),
                            "additions": _entero(añadidas),
                            "deletions": _entero(borradas),
                        }
                    )

                continue

            identificador, _, asunto = linea.partition(" ")

            commits.append(
                {
                    "hash": identificador.strip(),
                    "subject": asunto.strip(),
                    "files": [],
                }
            )

        return commits

    def is_git_repository(self) -> bool:
        return (self.repository / ".git").exists()

    def _run(
        self,
        *command: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=self.repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
