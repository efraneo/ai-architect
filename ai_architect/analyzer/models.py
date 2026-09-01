"""
Analyzer Models

Common data models used by the analyzer subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# =========================================================
# Python File Models
# =========================================================


@dataclass(slots=True)
class ImportInfo:
    """Represents one import statement."""

    module: str
    imported: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FunctionInfo:
    """Represents one function definition."""

    name: str
    line: int
    arguments: int
    decorators: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ClassInfo:
    """Represents one class definition."""

    name: str
    line: int
    methods: list[str] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PythonAnalysis:
    """Analysis result for a single Python file."""

    imports: list[ImportInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    total_lines: int = 0
    complexity: int = 0


# =========================================================
# Project Models
# =========================================================


@dataclass(slots=True)
class ProjectSummary:
    """High-level repository metrics."""

    total_files: int = 0
    python_files: int = 0
    total_classes: int = 0
    total_functions: int = 0
    dependency_modules: int = 0
    duplicate_groups: int = 0
    average_complexity: float = 0.0


@dataclass(slots=True)
class ProjectAnalysis:
    """
    Complete repository analysis.

    This object becomes the contract between
    Analyze → Review → Planner → Improve.
    """

    summary: ProjectSummary

    files: list[PythonAnalysis] = field(
        default_factory=list,
    )

    dependencies: dict[str, list[str]] = field(
        default_factory=dict,
    )

    duplicates: list[Any] = field(
        default_factory=list,
    )

    metrics: dict[str, Any] = field(
        default_factory=dict,
    )

    recommendations: list[str] = field(
        default_factory=list,
    )
