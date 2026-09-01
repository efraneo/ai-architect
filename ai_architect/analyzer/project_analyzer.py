"""
Project Analyzer

Central coordinator for repository analysis.
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.workspace.workspace_loader import WorkspaceLoader

from .class_analyzer import ClassAnalyzer
from .complexity_analyzer import ComplexityAnalyzer
from .dependency_analyzer import DependencyAnalyzer
from .duplicate_detector import DuplicateDetector
from .function_analyzer import FunctionAnalyzer
from .models import (
    ProjectAnalysis,
    ProjectSummary,
    PythonAnalysis,
)


class ProjectAnalyzer:
    """Coordinates all project-level analyzers."""

    def __init__(self) -> None:
        self.loader = WorkspaceLoader()
        self.class_analyzer = ClassAnalyzer()
        self.function_analyzer = FunctionAnalyzer()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.duplicate_detector = DuplicateDetector()

    def analyze(
        self,
        root: str | Path,
    ) -> ProjectAnalysis:
        """
        Analyze a repository and return ProjectAnalysis.

        ProjectAnalysis is the canonical contract produced
        by the analyzer subsystem.
        """

        root_path = Path(root).resolve()

        snapshot = self.loader.load(
            root_path,
        )

        python_files = [
            Path(file.path) for file in snapshot.files if file.extension == ".py"
        ]

        files = [
            self._analyze_file(
                file,
            )
            for file in python_files
        ]

        dependencies = self._analyze_dependencies(
            python_files,
        )

        duplicate_groups = self._duplicate_groups(
            root_path,
        )

        total_classes = sum(len(file_analysis.classes) for file_analysis in files)

        total_functions = sum(len(file_analysis.functions) for file_analysis in files)

        average_complexity = self._average_complexity(
            files,
        )

        summary = ProjectSummary(
            total_files=len(snapshot.files),
            python_files=len(python_files),
            total_classes=total_classes,
            total_functions=total_functions,
            dependency_modules=len(dependencies),
            duplicate_groups=duplicate_groups,
            average_complexity=average_complexity,
        )

        return ProjectAnalysis(
            summary=summary,
            files=files,
            dependencies=dependencies,
            duplicates=[],
            metrics=self._build_metrics(
                summary,
            ),
            recommendations=self._build_recommendations(
                summary,
            ),
        )

    # =====================================================
    # File Analysis
    # =====================================================

    def _analyze_file(
        self,
        file: Path,
    ) -> PythonAnalysis:
        """Analyze one Python file."""

        classes = self.class_analyzer.classes(
            file,
        )

        functions = self.function_analyzer.functions(
            file,
        )

        complexity = self.complexity_analyzer.score(
            file,
        )

        return PythonAnalysis(
            classes=list(classes),
            functions=list(functions),
            total_lines=self._line_count(
                file,
            ),
            complexity=int(complexity),
        )

    # =====================================================
    # Dependencies
    # =====================================================

    def _analyze_dependencies(
        self,
        files: list[Path],
    ) -> dict[str, list[str]]:
        """Build the project dependency mapping."""

        file_names = [str(file) for file in files]

        result = self.dependency_analyzer.analyze_project(
            file_names,
        )

        modules = getattr(
            result,
            "modules",
            result,
        )

        if not isinstance(
            modules,
            dict,
        ):
            return {}

        normalized: dict[str, list[str]] = {}

        for module, imports in modules.items():
            if isinstance(
                imports,
                list,
            ):
                normalized[str(module)] = [str(item) for item in imports]

        return normalized

    # =====================================================
    # Duplicates
    # =====================================================

    def _duplicate_groups(
        self,
        root: Path,
    ) -> int:
        """Return the number of duplicate groups."""

        result = self.duplicate_detector.duplicates(
            root,
        )

        return len(result)

    # =====================================================
    # Metrics
    # =====================================================

    @staticmethod
    def _line_count(
        file: Path,
    ) -> int:
        """Return the number of lines in a file."""

        try:
            return len(
                file.read_text(
                    encoding="utf-8",
                ).splitlines()
            )
        except OSError:
            return 0

    @staticmethod
    def _average_complexity(
        files: list[PythonAnalysis],
    ) -> float:
        """Calculate average file complexity."""

        if not files:
            return 0.0

        total = sum(file_analysis.complexity for file_analysis in files)

        return round(
            total / len(files),
            2,
        )

    @staticmethod
    def _build_metrics(
        summary: ProjectSummary,
    ) -> dict[str, object]:
        """Build normalized project metrics."""

        return {
            "total_files": summary.total_files,
            "python_files": summary.python_files,
            "total_classes": summary.total_classes,
            "total_functions": summary.total_functions,
            "dependency_modules": summary.dependency_modules,
            "duplicate_groups": summary.duplicate_groups,
            "average_complexity": summary.average_complexity,
        }

    @staticmethod
    def _build_recommendations(
        summary: ProjectSummary,
    ) -> list[str]:
        """Build basic analyzer recommendations."""

        recommendations: list[str] = []

        if summary.duplicate_groups > 0:
            recommendations.append(
                "Remove or consolidate duplicated code.",
            )

        if summary.average_complexity > 10:
            recommendations.append(
                "Reduce average code complexity.",
            )

        if not recommendations:
            recommendations.append(
                "No immediate structural recommendations.",
            )

        return recommendations
