"""
Decision Engine compatibility facade.

``AutoDecision`` is the canonical implementation.  This facade preserves the
older ``DecisionEngine.decide(...)`` API used by ProjectLoop and external
callers while routing all decisions through the institutional decision stack.
"""

from __future__ import annotations

from typing import Any

from ai_architect.core.context import AIContext

from .auto_decision import AutoDecision
from .decision_report import DecisionReport


class DecisionEngine:
    """Backward-compatible facade over :class:`AutoDecision`."""

    def __init__(self) -> None:
        self.engine = AutoDecision()

    def decide(
        self,
        metrics: dict[str, Any] | None = None,
        findings: list[str] | None = None,
        task: dict[str, Any] | None = None,
        tests_ok: bool = False,
        repository: str = "",
    ) -> dict[str, Any]:
        context = AIContext(repository=repository)
        context.metrics.update(metrics or {})
        context.validation["findings"] = list(findings or [])
        context.task.update(task or {})
        context.tests["success"] = bool(tests_ok)

        report = self.engine.evaluate(context)
        return report.to_dict()

    def evaluate(self, context: AIContext) -> DecisionReport:
        return self.engine.evaluate(context)

    def should_commit(self, report) -> bool:
        return self.engine.should_commit(report)

    def should_retry(self, report) -> bool:
        return self.engine.should_retry(report)

    def requires_review(self, report) -> bool:
        return self.engine.requires_review(report)

    def rejected(self, report) -> bool:
        return self.engine.rejected(report)

    def summary(self, report) -> str:
        return self.engine.summary(report)

    def diagnostics(self, report) -> dict[str, Any]:
        return self.engine.diagnostics(report)
