"""
=========================================================
Execution Task

Execution Task Domain Model
=========================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum


class TaskRisk(StrEnum):
    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class ExecutionTask:
    """
    Task metadata used during execution.

    This model describes the characteristics
    of a task being processed by the
    Execution Pipeline and Decision Engine.
    """

    ##########################################################
    # General
    ##########################################################

    name: str = ""

    description: str = ""

    ##########################################################
    # Impact
    ##########################################################

    touches_core: bool = False

    touches_api: bool = False

    touches_database: bool = False

    touches_security: bool = False

    ##########################################################
    # Risk
    ##########################################################

    risk: TaskRisk = TaskRisk.LOW

    ##########################################################
    # Execution
    ##########################################################

    estimated_seconds: int = 0

    retries: int = 0

    ##########################################################
    # Dependencies
    ##########################################################

    dependencies: list[str] = field(
        default_factory=list,
    )

    ##########################################################
    # Metadata
    ##########################################################

    metadata: dict = field(
        default_factory=dict,
    )

    ##########################################################

    @property
    def requires_review(
        self,
    ) -> bool:

        return self.touches_security or self.risk == TaskRisk.CRITICAL

    ##########################################################

    @property
    def is_complex(
        self,
    ) -> bool:

        return self.touches_core or self.touches_database or self.touches_security

    ##########################################################

    def add_dependency(
        self,
        dependency: str,
    ) -> None:

        if dependency not in self.dependencies:
            self.dependencies.append(
                dependency,
            )

    ##########################################################

    def to_dict(
        self,
    ) -> dict:

        data = asdict(
            self,
        )

        data["risk"] = self.risk.value

        return data
