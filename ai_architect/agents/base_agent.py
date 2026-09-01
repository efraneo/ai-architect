"""
=========================================================
Base Agent

Common Agent Interface
=========================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class BaseAgent(ABC):
    """
    Base class for every QUANT AI Architect agent.

    All agents (static or AI-powered) inherit from
    this class.
    """

    name = "Base Agent"

    version = "1.0"

    def __init__(self) -> None:

        self.created = datetime.utcnow()

    @abstractmethod
    def run(
        self,
        context,
    ):
        """
        Execute the agent.

        Must be implemented by AI agents.
        """

        raise NotImplementedError

    def review(
        self,
        project: str,
    ) -> dict:
        """
        Static agents may override this method.

        AI agents normally ignore it.
        """

        return {}

    def health(
        self,
    ) -> dict:

        return {
            "agent": self.name,
            "version": self.version,
            "status": "ready",
        }

    def capabilities(
        self,
    ) -> list[str]:

        return []

    def metadata(
        self,
    ) -> dict:

        return {
            "agent": self.name,
            "version": self.version,
            "created": self.created.isoformat(),
            "capabilities": self.capabilities(),
        }

    def execute(
        self,
        context,
    ):
        """
        Generic execution wrapper.

        Allows the AgentManager to invoke every
        agent uniformly.
        """

        return self.run(
            context,
        )
