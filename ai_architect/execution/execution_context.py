"""
=========================================================
Execution Context

Execution Pipeline Context
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ExecutionContext:
    """
    Shared execution context across the
    entire execution pipeline.

    This object travels through every
    execution stage, allowing each
    component to enrich the execution
    without tight coupling.
    """

    ##############################################################
    # Request
    ##############################################################

    repository: str

    filename: str

    instruction: str

    ##############################################################
    # Generation
    ##############################################################

    provider: str = ""

    generated_code: str = ""

    ##############################################################
    # Analysis
    ##############################################################

    metrics: dict[str, Any] = field(
        default_factory=dict,
    )

    task: dict[str, Any] = field(
        default_factory=dict,
    )

    ##############################################################
    # Validation
    ##############################################################

    validation_ok: bool = False

    findings: list[str] = field(
        default_factory=list,
    )

    ##############################################################
    # Testing
    ##############################################################

    tests_ok: bool = False

    ##############################################################
    # Decision
    ##############################################################

    decision: dict[str, Any] = field(
        default_factory=dict,
    )

    ##############################################################
    # Metadata
    ##############################################################

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    ##############################################################
    # Timing
    ##############################################################

    created_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    started_at: datetime | None = None

    finished_at: datetime | None = None

    ##############################################################

    def start(
        self,
    ) -> None:

        self.started_at = datetime.utcnow()

    ##############################################################

    def finish(
        self,
    ) -> None:

        self.finished_at = datetime.utcnow()

    ##############################################################

    def update(
        self,
        **kwargs: Any,
    ) -> None:

        for key, value in kwargs.items():
            if hasattr(
                self,
                key,
            ):
                setattr(
                    self,
                    key,
                    value,
                )

    ##############################################################

    @property
    def approved(
        self,
    ) -> bool:
        return bool(
            self.decision.get(
                "approved",
                False,
            )
        )

    ##############################################################

    @property
    def decision_name(
        self,
    ) -> str:
        value = self.decision.get(
            "decision",
            "UNKNOWN",
        )

        return str(value)

    ##############################################################

    @property
    def execution_time(
        self,
    ) -> float | None:

        if self.started_at is None or self.finished_at is None:
            return None

        return (self.finished_at - self.started_at).total_seconds()

    ##############################################################

    def to_dict(
        self,
    ) -> dict:

        return {
            "repository": self.repository,
            "filename": self.filename,
            "instruction": self.instruction,
            "provider": self.provider,
            "generated_code": self.generated_code,
            "metrics": self.metrics,
            "task": self.task,
            "validation_ok": self.validation_ok,
            "findings": self.findings,
            "tests_ok": self.tests_ok,
            "decision": self.decision,
            "metadata": self.metadata,
            "approved": self.approved,
            "decision_name": self.decision_name,
            "created_at": self.created_at.isoformat(),
            "started_at": (self.started_at.isoformat() if self.started_at else None),
            "finished_at": (self.finished_at.isoformat() if self.finished_at else None),
            "execution_time": self.execution_time,
        }
