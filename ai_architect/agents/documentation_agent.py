"""
=========================================================
Documentation Agent

AI Documentation Specialist
=========================================================
"""

from __future__ import annotations

from ai_architect.providers.provider_manager import (
    ProviderManager,
)

from .base_agent import BaseAgent


class DocumentationAgent(BaseAgent):
    name = "Documentation Agent"

    SYSTEM_PROMPT = """
You are the Documentation Specialist of QUANT AI Architect.

Responsibilities:

- Improve documentation.
- Keep docstrings updated.
- Generate API documentation.
- Improve README sections.
- Improve architecture documentation.
- Improve developer guides.
- Never modify business logic.

Return only the documentation analysis.
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

        report = self.provider.generate(
            prompt,
            temperature=0.15,
        )

        return {
            "agent": self.name,
            "provider": self.provider.name,
            "model": self.provider.model,
            "documentation": report,
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
                "Review all documentation and propose improvements.",
            ]
        )

    def capabilities(
        self,
    ) -> list[str]:

        return [
            "Docstrings",
            "README",
            "Architecture Docs",
            "API Documentation",
            "Developer Guides",
            "Markdown",
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
