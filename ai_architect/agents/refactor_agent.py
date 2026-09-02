"""
=========================================================
Refactor Agent

AI Refactoring Specialist
=========================================================
"""

from __future__ import annotations

from ai_architect.providers.provider_manager import (
    ProviderManager,
)

from .base_agent import BaseAgent


class RefactorAgent(BaseAgent):
    name = "Refactor Agent"

    SYSTEM_PROMPT = """
You are the Refactoring Specialist of QUANT AI Architect.

Your objectives:

- Improve maintainability.
- Preserve behavior.
- Preserve public APIs.
- Reduce complexity.
- Reduce duplication.
- Improve naming.
- Improve readability.
- Respect SOLID.
- Never introduce breaking changes.

Return only the refactoring proposal.
"""

    def __init__(self) -> None:

        self.provider = ProviderManager()

    def run(
        self,
        context: dict,
    ) -> dict:

        prompt = self._prompt(
            context,
        )

        proposal = self.provider.generate(
            prompt,
            temperature=0.15,
        )

        return {
            "agent": self.name,
            "provider": self.provider.name,
            "model": self.provider.model,
            "proposal": proposal,
            "status": "completed",
        }

    def _prompt(
        self,
        context: dict,
    ) -> str:

        return "\n\n".join(
            [
                self.SYSTEM_PROMPT.strip(),
                "PROJECT CONTEXT",
                str(context),
                "TASK",
                "Generate the safest possible refactoring plan.",
            ]
        )

    def capabilities(
        self,
    ) -> list[str]:

        return [
            "refactor",
            "SOLID",
            "Refactoring",
            "Clean Code",
            "Code Smells",
            "Complexity Reduction",
            "Duplication Removal",
            "Naming Improvements",
            "Architecture Preservation",
        ]

    def health(
        self,
    ) -> dict:

        return {
            "agent": self.name,
            "provider": self.provider.name,
            "model": self.provider.model,
            "available": self.provider.available(),
        }
