"""
=========================================================
Core Events

Internal Event Definitions
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Event:
    """
    Generic system event.
    """

    name: str

    source: str

    payload: dict[str, Any] = field(
        default_factory=dict,
    )

    timestamp: datetime = field(
        default_factory=datetime.utcnow,
    )


class Events:
    PLAN_CREATED = "PLAN_CREATED"

    TASK_CREATED = "TASK_CREATED"

    TASK_STARTED = "TASK_STARTED"

    TASK_COMPLETED = "TASK_COMPLETED"

    TASK_FAILED = "TASK_FAILED"

    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"

    VALIDATION_COMPLETED = "VALIDATION_COMPLETED"

    TESTS_COMPLETED = "TESTS_COMPLETED"

    DECISION_APPROVED = "DECISION_APPROVED"

    DECISION_REJECTED = "DECISION_REJECTED"

    COMMIT_CREATED = "COMMIT_CREATED"

    MEMORY_UPDATED = "MEMORY_UPDATED"

    LEARNING_COMPLETED = "LEARNING_COMPLETED"

    PIPELINE_FINISHED = "PIPELINE_FINISHED"
