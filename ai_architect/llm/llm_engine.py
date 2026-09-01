"""
=========================================================
LLM Engine

High-Level Interface
=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .workflow import LLMWorkflow


class LLMEngine:
    """
    High-level entry point for every LLM operation.

    The rest of the application communicates only with this
    class. It delegates the execution to the appropriate
    workflow.
    """

    def __init__(
        self,
        repository: str | Path,
        env_file: str,
    ) -> None:

        self.repository = Path(repository).resolve()

        self.workflow = LLMWorkflow(
            repository=self.repository,
            env_file=env_file,
        )

    @property
    def project(self) -> Path:

        return self.repository

    def improve(
        self,
        filename: str,
        instruction: str,
    ) -> dict[str, Any]:

        return self.workflow.execute(
            file=filename,
            task=instruction,
        )

    def review(
        self,
        filename: str,
    ) -> dict[str, Any]:

        return self.workflow.review(
            file=filename,
        )

    def refactor(
        self,
        filename: str,
        objective: str,
    ) -> dict[str, Any]:

        return self.workflow.refactor(
            file=filename,
            objective=objective,
        )
