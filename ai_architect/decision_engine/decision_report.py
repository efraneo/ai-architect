"""
=========================================================
Decision Report

Decision Engine Result Model
=========================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class DecisionType(StrEnum):
    ACCEPT = "ACCEPT"

    RETRY = "RETRY"

    MANUAL_REVIEW = "MANUAL_REVIEW"

    REJECT = "REJECT"


@dataclass(slots=True)
class DecisionReport:
    """
    Result produced by the Decision Engine.

    This object is exchanged between
    ExecutionPipeline, MemoryEngine,
    Planner and Reporting.
    """

    ##########################################################
    # Decision
    ##########################################################

    decision: DecisionType

    approved: bool

    confidence: float

    ##########################################################
    # Explanation
    ##########################################################

    reason: str = ""

    ##########################################################
    # Findings
    ##########################################################

    findings: list[str] = field(
        default_factory=list,
    )

    ##########################################################
    # Metrics Snapshot
    ##########################################################

    metrics: dict[str, Any] = field(
        default_factory=dict,
    )

    ##########################################################
    # Metadata
    ##########################################################

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    ##########################################################
    # Timing
    ##########################################################

    created_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    ##########################################################

    @property
    def retry_required(
        self,
    ) -> bool:

        return self.decision == DecisionType.RETRY

    ##########################################################

    @property
    def manual_review(
        self,
    ) -> bool:

        return self.decision == DecisionType.MANUAL_REVIEW

    ##########################################################

    @property
    def rejected(
        self,
    ) -> bool:

        return self.decision == DecisionType.REJECT

    ##########################################################

    @property
    def accepted(
        self,
    ) -> bool:

        return self.decision == DecisionType.ACCEPT

    ##########################################################

    def to_dict(
        self,
    ) -> dict[str, Any]:

        data = asdict(
            self,
        )

        data["decision"] = self.decision.value

        data["created_at"] = self.created_at.isoformat()

        return data
