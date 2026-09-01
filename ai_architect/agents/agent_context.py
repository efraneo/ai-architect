"""
=========================================================
Agent Context

Shared Context Between All Agents
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class AgentContext:
    """
    Shared execution context used by every agent.

    This object becomes the single source of truth
    during one execution of QUANT AI Architect.
    """

    repository: str

    created: datetime = field(
        default_factory=datetime.utcnow,
    )

    data: dict[str, Any] = field(
        default_factory=dict,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    logs: list[str] = field(
        default_factory=list,
    )

    warnings: list[str] = field(
        default_factory=list,
    )

    errors: list[str] = field(
        default_factory=list,
    )

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.data[key] = value

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.data.get(
            key,
            default,
        )

    def has(
        self,
        key: str,
    ) -> bool:

        return key in self.data

    def update(
        self,
        values: dict,
    ) -> None:

        self.data.update(values)

    def merge(
        self,
        values: dict,
    ) -> None:

        self.data.update(values)

    def add_log(
        self,
        message: str,
    ) -> None:

        self.logs.append(message)

    def add_warning(
        self,
        message: str,
    ) -> None:

        self.warnings.append(message)

    def add_error(
        self,
        message: str,
    ) -> None:

        self.errors.append(message)

    def summary(
        self,
    ) -> dict:

        return {
            "repository": self.repository,
            "created": self.created.isoformat(),
            "sections": sorted(
                self.data.keys(),
            ),
            "items": len(
                self.data,
            ),
            "logs": len(
                self.logs,
            ),
            "warnings": len(
                self.warnings,
            ),
            "errors": len(
                self.errors,
            ),
        }

    def export(
        self,
    ) -> dict:

        return {
            "repository": self.repository,
            "created": self.created.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "logs": self.logs,
            "warnings": self.warnings,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(
        cls,
        repository: str,
        values: dict,
    ) -> AgentContext:

        context = cls(repository)

        context.data.update(values)

        return context
