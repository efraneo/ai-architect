"""
=========================================================
Code Reviewer Agent

AI Code Review Specialist
=========================================================
"""

from __future__ import annotations

from ai_architect.providers.provider_manager import (
    ProviderManager,
)

from .base_agent import BaseAgent


class CodeReviewerAgent(BaseAgent):
    name = "Code Reviewer Agent"

    SYSTEM_PROMPT = """
You are the Code Reviewer of QUANT AI Architect.

Review the supplied source code.

Evaluate:

- Bugs
- SOLID
- Readability
- Maintainability
- Performance
- Security
- Dead code
- Code smells

Return a structured review only.
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

        review = self.provider.generate(
            prompt,
            temperature=0.10,
        )

        return {
            "agent": self.name,
            "provider": self.provider.name,
            "model": self.provider.model,
            "review": review,
            "status": "completed",
        }

    def _prompt(
        self,
        context: dict,
    ) -> str:

        return "\n\n".join(
            [
                self.SYSTEM_PROMPT.strip(),
                "CONTEXT",
                str(context),
                "TASK",
                "Perform a professional code review.",
            ]
        )

    def capabilities(
        self,
    ) -> list[str]:

        return [
            "Bug Detection",
            "Security Review",
            "SOLID Validation",
            "Performance Review",
            "Readability Review",
            "Maintainability Review",
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
