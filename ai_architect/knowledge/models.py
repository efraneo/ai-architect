"""
============================================================
QUANT TITAN AI ARCHITECT

knowledge/models.py

Modelos centrales del Knowledge Engine.

Todos los analizadores producen estos modelos.
Todos los revisores consumen estos modelos.

Reglas:

- Una única responsabilidad.
- Sin lógica de negocio.
- Solo dataclasses.
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ==========================================================
# ARCHIVO
# ==========================================================


@dataclass(slots=True)
class FileInfo:
    """
    Información de un archivo del proyecto.
    """

    path: Path

    module: str

    extension: str

    size_bytes: int

    line_count: int

    class_count: int

    function_count: int

    import_count: int

    last_modified: datetime


# ==========================================================
# SÍMBOLO
# ==========================================================


@dataclass(slots=True)
class SymbolInfo:
    """
    Clase, función o constante encontrada.
    """

    name: str

    symbol_type: str

    module: str

    file: Path

    line: int


# ==========================================================
# DEPENDENCIA
# ==========================================================


@dataclass(slots=True)
class DependencyInfo:
    """
    Relación entre dos módulos.
    """

    source: str

    target: str

    dependency_type: str


# ==========================================================
# MÓDULO
# ==========================================================


@dataclass(slots=True)
class ModuleInfo:
    """
    Información agregada de un módulo.
    """

    name: str

    path: Path

    files: list[FileInfo] = field(default_factory=list)


# ==========================================================
# SNAPSHOT
# ==========================================================


@dataclass(slots=True)
class ProjectSnapshot:
    """
    Fotografía completa del proyecto.
    """

    generated_at: datetime

    root: Path

    total_files: int

    python_files: int

    total_lines: int

    total_classes: int

    total_functions: int

    total_imports: int

    duplicated_symbols: int

    duplicated_modules: int

    oversized_files: int

    files: list[FileInfo] = field(default_factory=list)

    modules: list[ModuleInfo] = field(default_factory=list)


# ==========================================================
# CALIDAD
# ==========================================================


@dataclass(slots=True)
class QualityScore:
    """
    Puntuación arquitectónica.
    """

    architecture: float

    maintainability: float

    complexity: float

    typing: float

    documentation: float

    duplication: float

    testing: float

    overall: float
