"""
Code Reviewer
"""

from __future__ import annotations

from .openai_client import OpenAIClient


class CodeReviewer:
    def __init__(self) -> None:
        self.client = OpenAIClient()

    def review(
        self,
        source: str,
    ) -> str:
        system_prompt = """
You are QUANT AI Architect, an autonomous senior
software engineer and code reviewer.

Review the supplied source code for:

- correctness
- architecture
- maintainability
- typing
- security
- error handling
- performance
- testability

Return concise, actionable findings.
Prioritize real defects over stylistic preferences.
""".strip()

        return self.client.ask(
            prompt=source,
            system=system_prompt,
        )
