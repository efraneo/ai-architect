"""
=========================================================
AI Context

Execution Backbone
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai_architect.core.events import Event
from ai_architect.core.metadata import Metadata


@dataclass(slots=True)
class AIContext:
    """
    Shared execution context.

    Every module reads and writes here.
    """

    repository: str

    metadata: Metadata = field(
        default_factory=Metadata,
    )

    #
    # Repository
    #

    analysis: dict = field(
        default_factory=dict,
    )

    #
    # Current Task
    #

    task: dict = field(
        default_factory=dict,
    )

    #
    # Planner
    #

    plan: Any = None

    tasks: list = field(
        default_factory=list,
    )

    #
    # Validation
    #

    validation: dict = field(
        default_factory=dict,
    )

    #
    # Tests
    #

    tests: dict = field(
        default_factory=dict,
    )

    #
    # Decision
    #

    decision: dict = field(
        default_factory=dict,
    )

    #
    # Memory
    #

    memory: dict = field(
        default_factory=dict,
    )

    learning: dict = field(
        default_factory=dict,
    )

    #
    # Git
    #

    git: dict = field(
        default_factory=dict,
    )

    #
    # LLM
    #

    llm: dict = field(
        default_factory=dict,
    )

    #
    # Execution
    #

    execution: dict = field(
        default_factory=dict,
    )

    #
    # Shared Metrics
    #

    metrics: dict = field(
        default_factory=dict,
    )

    #
    # Event Bus
    #

    events: list[Event] = field(
        default_factory=list,
    )

    #
    # Generic Store
    #

    data: dict[str, Any] = field(
        default_factory=dict,
    )

    # -----------------------------------------------------
    # Event
    # -----------------------------------------------------

    def emit(
        self,
        name: str,
        source: str,
        **payload,
    ):

        self.events.append(
            Event(
                name=name,
                source=source,
                payload=payload,
            )
        )

    # -----------------------------------------------------
    # Generic Store
    # -----------------------------------------------------

    def put(
        self,
        key: str,
        value: Any,
    ):

        self.data[key] = value

    # -----------------------------------------------------

    def get(
        self,
        key: str,
        default=None,
    ):

        return self.data.get(
            key,
            default,
        )

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    def update_metrics(
        self,
        values: dict,
    ):

        self.metrics.update(
            values,
        )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    def summary(
        self,
    ):

        return {
            "repository": self.repository,
            "tasks": len(self.tasks),
            "events": len(self.events),
            "metrics": len(self.metrics),
            "analysis": bool(self.analysis),
            "task": bool(self.task),
            "validation": bool(self.validation),
            "tests": bool(self.tests),
            "decision": bool(self.decision),
        }
