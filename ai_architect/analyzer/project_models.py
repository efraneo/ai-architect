"""
=========================================================
Project Analysis Models
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProjectSummary:
    total_files: int = 0

    python_files: int = 0

    total_classes: int = 0

    total_functions: int = 0

    dependency_modules: int = 0

    duplicate_groups: int = 0

    average_complexity: float = 0.0


@dataclass(slots=True)
class ProjectAnalysis:
    summary: ProjectSummary

    files: list[Any] = field(default_factory=list)

    dependencies: dict[str, list[str]] = field(default_factory=dict)

    duplicates: list[Any] = field(default_factory=list)

    metrics: dict[str, Any] = field(default_factory=dict)

    recommendations: list[str] = field(default_factory=list)
