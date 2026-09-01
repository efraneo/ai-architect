"""
=========================================================
AI Architect Orchestrator
=========================================================
"""

from __future__ import annotations

from ai_architect.execution_context import (
    ExecutionContext,
)
from ai_architect.pipeline import (
    Pipeline,
)


class Orchestrator:
    def __init__(
        self,
        context: ExecutionContext,
    ):

        self.context = context

        self.pipeline = Pipeline(context)

    def execute(self):

        self.context.logger.info("Starting orchestration...")

        result = self.pipeline.run()

        self.context.logger.info("Pipeline finished.")

        return result
