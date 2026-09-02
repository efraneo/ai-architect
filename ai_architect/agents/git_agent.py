from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ai_architect.git.status_manager import StatusManager
from ai_architect.git.tag_manager import TagManager

from .base_agent import BaseAgent

TIEMPO_LIMITE = 30


class GitAgent(BaseAgent):
    """Estado del repositorio.

    Tenía su propia lectura de ``git status``: contaba solo las líneas que
    empiezan por ``" M"`` o ``"M "``, así que se perdía los ``MM`` (modificado
    en el índice y en el árbol) y los ``AM``, no veía renombrados ni
    conflictos, y llamaba a git **dos veces** para el mismo estado --
    ``_modified()`` y ``_untracked()`` ejecutaban ``_status()`` cada uno.

    Ahora usa el lector de ``git/``, que es el mismo que usa ``GitManager``.
    """

    name = "Git Agent"

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
        project_path = Path(project)

        if not (project_path / ".git").exists():
            return {
                "agent": self.name,
                "git": False,
                "status": "NOT_A_GIT_REPOSITORY",
            }

        estado = StatusManager(project_path).status()

        etiquetas = TagManager(project_path)

        informe: dict[str, Any] = {
            "agent": self.name,
            "git": True,
            "branch": estado.branch,
            "clean": estado.clean,
            "modified": len(estado.modified),
            "created": len(estado.created),
            "deleted": len(estado.deleted),
            "renamed": len(estado.renamed),
            "untracked": len(estado.untracked),
            "conflicted": len(estado.conflicted),
            "pending": estado.total,
            "ahead": self._ahead(project_path),
            "behind": self._behind(project_path),
            "latest_tag": etiquetas.latest(),
            "last_commit": self._last_commit(project_path),
            "recent_commits": self._recent_commits(project_path),
            "status": "OK",
        }

        # Un conflicto sin resolver no es una estadística: es algo que hay que
        # arreglar antes de que nadie genere un parche encima.
        if estado.conflicted:
            informe["findings"] = [
                {
                    "type": "conflicto",
                    "file": ruta,
                    "issue": "conflicto de fusión sin resolver",
                }
                for ruta in estado.conflicted
            ]

        return informe

    def _git(
        self,
        project: Path,
        *args: str,
    ) -> str:
        try:
            result = subprocess.run(
                [
                    "git",
                    *args,
                ],
                cwd=project,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                timeout=TIEMPO_LIMITE,
            )

            return result.stdout.strip()

        except Exception:
            return ""

    def _seguimiento(
        self,
        project: Path,
    ) -> tuple[int, int]:
        """Cuánto le falta y cuánto le sobra respecto a la rama remota.

        Sin rama de seguimiento no hay nada que comparar, y eso es normal en
        una rama recién creada: cero y cero, no un error.
        """
        output = self._git(
            project,
            "rev-list",
            "--left-right",
            "--count",
            "@{upstream}...HEAD",
        )

        partes = output.split()

        if len(partes) != 2:
            return 0, 0

        try:
            return int(partes[0]), int(partes[1])

        except ValueError:
            return 0, 0

    def _ahead(
        self,
        project: Path,
    ) -> int:
        return self._seguimiento(project)[1]

    def _behind(
        self,
        project: Path,
    ) -> int:
        return self._seguimiento(project)[0]

    def _last_commit(
        self,
        project: Path,
    ) -> str:
        return self._git(
            project,
            "log",
            "-1",
            "--pretty=%h %s",
        )

    def _recent_commits(
        self,
        project: Path,
        count: int = 5,
    ) -> list[str]:
        output = self._git(
            project,
            "log",
            f"-{count}",
            "--pretty=%h %s",
        )

        return output.splitlines() if output else []

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "git",
            "Branch Detection",
            "Repository Status",
            "Modified Files",
            "Untracked Files",
            "Conflict Detection",
            "Tag Detection",
            "Commit History",
            "Ahead/Behind Analysis",
        ]
