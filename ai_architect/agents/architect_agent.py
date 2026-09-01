"""
Compatibility Architect Agent.

This module is the AgentManager-facing adapter for the architecture
capability.  It talks to the provider through ``ProviderManager`` and keeps
the common ``BaseAgent.run(context)`` contract used by AgentManager.

It used to point at ``ai_architect.llm``, which held an earlier and simpler
version of the providers. That package was removed; the code had already
migrated to ``ai_architect.providers``.
"""

from __future__ import annotations

from ai_architect.providers.provider_manager import ProviderManager

from .base_agent import BaseAgent


class ArchitectAgent(BaseAgent):
    name = "Architect Agent"

    SYSTEM_PROMPT = """
You are the Senior Software Architect of AI Architect.

Review the supplied repository context and return a concise architectural
assessment and implementation recommendations. Preserve public APIs, identify
high-risk integration issues, and prefer the smallest safe change.
""".strip()

    def __init__(self) -> None:
        self.provider = ProviderManager()

    def run(self, context: dict) -> dict:
        prompt = "\n\n".join(
            [
                self.SYSTEM_PROMPT,
                "PROJECT CONTEXT",
                str(context),
            ]
        )
        report = self.provider.generate(prompt, temperature=0.10)
        return {
            "agent": self.name,
            "provider": self.provider.name,
            "model": self.provider.model,
            "architecture": report,
            "status": "completed",
        }

    def capabilities(self) -> list[str]:
        return [
            "Architecture Review",
            "Integration Analysis",
            "API Preservation",
            "Risk Assessment",
        ]

    def health(self) -> dict:
        return {
            "agent": self.name,
            "provider": self.provider.name,
            "model": self.provider.model,
            "available": self.provider.available(),
        }
