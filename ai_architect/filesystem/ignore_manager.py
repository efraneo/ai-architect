"""
=========================================================
Ignore Manager

Qué no es del proyecto.
=========================================================

Estaba huérfano y era la misma lista fija que ya tenía ``constants.py``,
solo que envuelta en un objeto. Al compararla con el ``.gitignore`` de este
mismo repositorio apareció el hueco:

    ignorados por git pero NO por los agentes:
    htmlcov, .ai_architect, workspace, memory/db,
    knowledge/cache, repository/cache, ...

Cada proyecto ignora sus propias carpetas —``target/``, ``out/``,
``.next/``, una carpeta de datos— y los agentes las recorrían todas. Es el
mismo problema del ``.venv``, pero en los proyectos ajenos.

**Solo se aplica a carpetas, no a archivos sueltos.** Una carpeta en el
``.gitignore`` es salida de compilación o caché: nunca es algo que quieras
analizar. Un archivo suelto puede ser justo lo contrario: ``.env`` está
ignorado por git en casi todos los proyectos, y es **exactamente** donde el
agente de seguridad tiene que mirar para encontrar una clave filtrada.
"""

from __future__ import annotations

from pathlib import Path

from .constants import (
    DEFAULT_IGNORED_DIRECTORIES,
    DEFAULT_IGNORED_FILES,
)


class IgnoreManager:
    def __init__(
        self,
        ignored_directories: set[str] | None = None,
        ignored_files: set[str] | None = None,
    ) -> None:
        self.directories = set(ignored_directories or DEFAULT_IGNORED_DIRECTORIES)

        self.files = set(ignored_files or DEFAULT_IGNORED_FILES)

    @classmethod
    def for_project(
        cls,
        root: str | Path,
    ) -> IgnoreManager:
        """La lista de siempre, más lo que ignora el ``.gitignore`` del proyecto."""
        gestor = cls()

        for carpeta in leer_carpetas_ignoradas(Path(root) / ".gitignore"):
            gestor.ignore_directory(carpeta)

        return gestor

    def ignore_directory(
        self,
        directory: str,
    ) -> None:
        self.directories.add(directory)

    def ignore_file(
        self,
        filename: str,
    ) -> None:
        self.files.add(filename)

    def should_ignore(
        self,
        path: Path,
    ) -> bool:
        """¿Está esto fuera del proyecto?"""
        if path.name in self.files:
            return True

        return any(part in self.directories for part in path.parts)

    def export(self) -> dict:
        return {
            "directories": sorted(self.directories),
            "files": sorted(self.files),
        }


def leer_carpetas_ignoradas(gitignore: Path) -> set[str]:
    """Las carpetas que declara un ``.gitignore``.

    Se lee un subconjunto deliberadamente conservador: nombres de carpeta
    tal cual, con o sin barra final. Lo que no se entienda —comodines,
    negaciones con ``!``, rutas con barras intermedias— **se descarta**,
    porque interpretarlo a medias sería peor que no leerlo: se acabaría
    dejando fuera código que sí es del proyecto.
    """
    if not gitignore.is_file():
        return set()

    try:
        lineas = gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()

    except OSError:
        return set()

    carpetas: set[str] = set()

    for linea in lineas:
        patron = linea.strip()

        if not patron or patron.startswith("#") or patron.startswith("!"):
            continue

        # Una entrada de carpeta acaba en barra. Sin ella no se sabe si es
        # carpeta o archivo, así que solo se acepta un nombre simple sin
        # extensión -- ``.env`` no entra, y eso es lo que se busca.
        es_carpeta = patron.endswith("/")

        nombre = patron.rstrip("/").lstrip("/")

        if not nombre or any(c in nombre for c in "*?[]") or "/" in nombre:
            continue

        if es_carpeta or "." not in nombre:
            carpetas.add(nombre)

    return carpetas
