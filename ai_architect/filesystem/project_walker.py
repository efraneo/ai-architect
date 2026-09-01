"""
============================================================
QUANT TITAN AI ARCHITECT

filesystem/project_walker.py

Responsabilidad:
----------------
Recorrer el proyecto de forma segura.

Este módulo NO analiza código.

Únicamente descubre archivos y carpetas.

Será utilizado por:

- ProjectSnapshot
- DependencyAnalyzer
- SymbolIndexer
- DuplicateDetector
- ComplexityAnalyzer

Principios:

- Una única responsabilidad.
- Sin lógica de negocio.
- Sin dependencias del resto del sistema.
============================================================
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

DEFAULT_IGNORED_DIRECTORIES = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    "node_modules",
    ".DS_Store",
}


DEFAULT_ALLOWED_EXTENSIONS = {".py", ".yaml", ".yml", ".toml", ".json", ".md"}


@dataclass(slots=True)
class ProjectFile:
    """
    Representa un archivo encontrado.
    """

    path: Path

    relative_path: Path

    extension: str

    size_bytes: int


class ProjectWalker:
    """
    Recorre el proyecto.

    No interpreta el contenido.
    """

    def __init__(
        self,
        root: Path,
        ignored_directories: set[str] | None = None,
        allowed_extensions: set[str] | None = None,
    ):

        self.root = root.resolve()

        self.ignored = ignored_directories or DEFAULT_IGNORED_DIRECTORIES

        self.extensions = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS

    def walk(self) -> Iterator[ProjectFile]:
        """
        Recorre todos los archivos válidos.
        """

        for file in self.root.rglob("*"):
            if not file.is_file():
                continue

            if self._is_ignored(file):
                continue

            if file.suffix.lower() not in self.extensions:
                continue

            yield ProjectFile(
                path=file,
                relative_path=file.relative_to(self.root),
                extension=file.suffix.lower(),
                size_bytes=file.stat().st_size,
            )

    def count(self) -> int:
        """
        Número de archivos encontrados.
        """

        return sum(1 for _ in self.walk())

    def _is_ignored(self, file: Path) -> bool:
        """
        Verifica si pertenece a una carpeta ignorada.
        """

        return any(part in self.ignored for part in file.parts)
