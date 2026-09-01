"""
=========================================================
Test Agent
=========================================================
"""

from __future__ import annotations

from .openai_client import OpenAIClient
from .prompt_builder import PromptBuilder


class TestAgent:
    def __init__(self):

        self.client = OpenAIClient()

        self.prompts = PromptBuilder()

    def generate_tests(
        self,
        source: str,
    ) -> str:

        prompt = f"""
Generate pytest unit tests.

Requirements

- pytest
- typed
- edge cases
- high coverage

Code

{source}
"""

        return self.client.ask(
            prompt=prompt,
            system=self.prompts.system_prompt(),
        )

    def improve_tests(
        self,
        existing_tests: str,
    ) -> str:

        prompt = f"""
Improve these tests.

{existing_tests}
"""

        return self.client.ask(
            prompt=prompt,
            system=self.prompts.system_prompt(),
        )
