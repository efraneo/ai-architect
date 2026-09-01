"""
============================================================
QUANT TITAN AI ARCHITECT

workspace/workspace.py

Workspace central del Arquitecto IA.

Representa el estado completo del proyecto en memoria.

Ningún módulo debe recorrer nuevamente el proyecto.

Todos consumirán este Workspace.

============================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ai_architect.filesystem.project_walker import (
    ProjectFile
)


@dataclass(slots=True)
class Workspace:
    """
    Estado completo del proyecto.

    Vive en memoria durante un ciclo completo
    de análisis.
    """

    root: Path

    created_at: datetime

    files: list[ProjectFile] = field(default_factory=list)

    modules: dict = field(default_factory=dict)

    dependencies: dict = field(default_factory=dict)

    symbols: dict = field(default_factory=dict)

    metrics: dict = field(default_factory=dict)

    metadata: dict = field(default_factory=dict)

    def total_files(self) -> int:
        """
        Número total de archivos.
        """
        return len(self.files)

    def python_files(self) -> int:
        """
        Cantidad de archivos Python.
        """
        return sum(
            1
            for file in self.files
            if file.extension == ".py"
        )

    def total_size(self) -> int:
        """
        Tamaño total del proyecto.
        """
        return sum(
            file.size_bytes
            for file in self.files
        )

    def clear(self) -> None:
        """
        Limpia completamente el Workspace.
        """
        self.files.clear()
        self.modules.clear()
        self.dependencies.clear()
        self.symbols.clear()
        self.metrics.clear()
        self.metadata.clear()
