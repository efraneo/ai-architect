"""
Compatibility Test Agent.

This adapter exposes the AgentManager ``BaseAgent.run(context)`` contract
for test generation, talking to the provider through ``ProviderManager``.

It used to point at ``ai_architect.llm.test_agent``, an earlier version that
was removed; the code had already migrated to ``ai_architect.providers``.
"""

from __future__ import annotations

from ai_architect.providers.provider_manager import ProviderManager

from .base_agent import BaseAgent


class TestAgent(BaseAgent):
    name = "Test Agent"

    SYSTEM_PROMPT = """
You are the Testing Specialist of AI Architect.

Review the supplied repository context and propose pytest coverage for the
highest-risk behavior. Focus on integration boundaries, negative paths, and
regression tests. Do not modify production code.
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
            "tests": report,
            "status": "completed",
        }

    def capabilities(self) -> list[str]:
        return [
            "Pytest",
            "Regression Testing",
            "Boundary Testing",
            "Coverage Analysis",
        ]

    def health(self) -> dict:
        return {
            "agent": self.name,
            "provider": self.provider.name,
            "model": self.provider.model,
            "available": self.provider.available(),
        }
