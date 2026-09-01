"""
Execution Result

Execution Pipeline Result Models
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from ai_architect.decision_engine.decision_report import DecisionReport
from ai_architect.execution.repository_metrics import RepositoryMetrics


@dataclass(slots=True)
class ExecutionResult:
    """
    Final result produced by the execution subsystem.
    """

    repository: str
    filename: str
    instruction: str

    success: bool = False
    provider: str = ""
    generated_code: str = ""
    validation_ok: bool = False
    findings: list[str] = field(default_factory=list)
    tests_ok: bool = False
    decision: DecisionReport | None = None
    metrics: RepositoryMetrics = field(default_factory=RepositoryMetrics)
    metadata: dict[str, Any] = field(default_factory=dict)

    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    duration: float = 0.0

    def finish(self) -> None:
        self.finished_at = datetime.utcnow()
        self.duration = round(
            (self.finished_at - self.started_at).total_seconds(),
            3,
        )

    @property
    def approved(self) -> bool:
        if self.decision is not None:
            return self.decision.approved

        return bool(
            self.metadata.get("execution", {}).get(
                "approved",
                self.validation_ok and self.success,
            )
        )

    @property
    def confidence(self) -> float:
        if self.decision is None:
            return 0.0

        return self.decision.confidence

    @property
    def decision_name(self) -> str:
        if self.decision is not None:
            return self.decision.decision.value

        if self.approved:
            return "ACCEPT"

        return "REJECT"

    @property
    def completed(self) -> bool:
        return self.finished_at is not None

    @property
    def execution_time(self) -> float:
        return self.duration

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)

        if self.decision is not None:
            data["decision"] = self.decision.to_dict()
        else:
            data["decision"] = None

        data["metrics"] = self.metrics.to_dict()
        data["started_at"] = self.started_at.isoformat()
        data["finished_at"] = self.finished_at.isoformat() if self.finished_at else None

        return data

    def summary(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "file": self.filename,
            "success": self.success,
            "approved": self.approved,
            "decision": self.decision_name,
            "confidence": self.confidence,
            "validation": self.validation_ok,
            "tests": self.tests_ok,
            "provider": self.provider,
            "duration": self.duration,
        }

    def __bool__(self) -> bool:
        return self.success
