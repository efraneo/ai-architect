"""
=========================================================
Repository Metrics

Repository Quality Metrics
=========================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class RepositoryMetrics:
    """
    Repository quality metrics collected during analysis.

    This model centralizes all repository quality
    indicators used across the execution pipeline.
    """

    ##########################################################
    # Code Quality
    ##########################################################

    duplicates: int = 0

    oversized_files: int = 0

    complexity: float = 0.0

    ##########################################################
    # Security
    ##########################################################

    security_findings: int = 0

    ##########################################################
    # Testing
    ##########################################################

    coverage: float = 100.0

    failed_tests: int = 0

    ##########################################################
    # Architecture
    ##########################################################

    dependency_cycles: int = 0

    circular_imports: int = 0

    ##########################################################
    # Documentation
    ##########################################################

    undocumented_objects: int = 0

    ##########################################################
    # Extensible metadata
    ##########################################################

    metadata: dict = field(
        default_factory=dict,
    )

    ##########################################################

    @property
    def healthy(
        self,
    ) -> bool:

        return (
            self.duplicates == 0
            and self.security_findings == 0
            and self.complexity < 10
        )

    ##########################################################

    @property
    def risk_score(
        self,
    ) -> float:

        score = 0.0

        score += self.duplicates * 1.5

        score += self.security_findings * 10

        score += self.complexity

        score += self.dependency_cycles * 3

        score += self.circular_imports * 2

        score += self.failed_tests * 5

        return round(
            score,
            2,
        )

    ##########################################################

    def merge(
        self,
        other: RepositoryMetrics,
    ) -> None:

        self.duplicates += other.duplicates

        self.oversized_files += other.oversized_files

        self.security_findings += other.security_findings

        self.failed_tests += other.failed_tests

        self.dependency_cycles += other.dependency_cycles

        self.circular_imports += other.circular_imports

        self.undocumented_objects += other.undocumented_objects

        self.complexity = max(
            self.complexity,
            other.complexity,
        )

        self.coverage = min(
            self.coverage,
            other.coverage,
        )

        self.metadata.update(
            other.metadata,
        )

    ##########################################################

    def to_dict(
        self,
    ) -> dict:

        return asdict(
            self,
        )
