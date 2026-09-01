"""
=========================================================
ChangeLog Command

Generar el CHANGELOG desde el historial de git.
=========================================================

`changelog/` estaba huérfano, y mientras tanto el `ReleaseAgent` —conectado
en el PR #8— reporta en cada inspección:

    release: no hay CHANGELOG: nadie sabe qué cambió entre versiones

Esto lo llena.

**No escribe nada salvo que se le pida con ``--write``.** Un comando que
modifica un archivo del repositorio por el mero hecho de ejecutarlo es una
sorpresa desagradable; se ve primero, se escribe después.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.changelog.changelog_builder import ChangeLogBuilder
from ai_architect.changelog.changelog_writer import ChangeLogWriter

NOMBRE = "CHANGELOG.md"


def run(
    project: str,
    version: str = "",
    author: str = "AI Architect",
    write: bool = False,
    since: str | None = None,
) -> dict:
    """Construye la entrada de changelog de esta versión.

    Parameters
    ----------
    project:
        Raíz del repositorio.
    version:
        Cómo llamar a esta versión. Si no se da, se usa la última etiqueta
        más un aviso.
    write:
        Escribir en ``CHANGELOG.md``. Apagado por defecto.
    since:
        Desde qué referencia contar. Por defecto, la última etiqueta.
    """

    repository = Path(project).resolve()

    if not repository.exists():
        return {
            "success": False,
            "repository": str(repository),
            "error": "Repository not found.",
        }

    if not (repository / ".git").exists():
        return {
            "success": False,
            "repository": str(repository),
            "error": "Not a git repository.",
        }

    builder = ChangeLogBuilder(repository)

    desde = builder.desde_la_ultima_etiqueta() if since is None else since

    entrada = builder.build(
        version=version,
        author=author,
        since=since,
    )

    escritor = ChangeLogWriter()

    destino = repository / NOMBRE

    resultado: dict[str, Any] = {
        "success": True,
        "repository": str(repository),
        "version": entrada.version,
        "since": desde or "(todo el historial)",
        "total_changes": entrada.total_changes,
        "by_type": _por_tipo(entrada),
        "written": False,
        "file": str(destino),
        "preview": escritor.render(entrada),
    }

    if write:
        escritor.write(entrada, destino)
        resultado["written"] = True

    return resultado


def _por_tipo(entrada) -> dict[str, int]:
    """Cuántos cambios de cada clase, para no leerse el bloque entero."""
    cuenta: dict[str, int] = {}

    for item in entrada.changes:
        clave = str(item.change_type)

        cuenta[clave] = cuenta.get(clave, 0) + 1

    return dict(sorted(cuenta.items()))
