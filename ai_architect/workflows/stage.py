"""
=========================================================
Workflow Stage
=========================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .stage_result import StageResult


class Stage(ABC):
    def __init__(
        self,
        name: str,
    ):

        self.name = name

    @abstractmethod
    def execute(
        self,
        context,
    ) -> StageResult: ...
