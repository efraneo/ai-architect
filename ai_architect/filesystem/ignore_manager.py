"""
=========================================================
Ignore Manager

Gestiona qué archivos y carpetas deben
ser ignorados durante el análisis.
=========================================================
"""

from pathlib import Path

from .constants import (
    DEFAULT_IGNORED_DIRECTORIES,
    DEFAULT_IGNORED_FILES,
)


class IgnoreManager:
    def __init__(
        self,
        ignored_directories=None,
        ignored_files=None,
    ):

        self.directories = set(ignored_directories or DEFAULT_IGNORED_DIRECTORIES)

        self.files = set(ignored_files or DEFAULT_IGNORED_FILES)

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
        """
        Determina si un archivo
        debe ser ignorado.
        """

        if path.name in self.files:
            return True

        return any(part in self.directories for part in path.parts)

    def export(self) -> dict:
        """
        Exporta la configuración
        actual.
        """

        return {
            "directories": sorted(self.directories),
            "files": sorted(self.files),
        }
