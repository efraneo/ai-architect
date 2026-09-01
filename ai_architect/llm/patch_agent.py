"""
=========================================================
Patch Agent
=========================================================
"""

from __future__ import annotations

from .context_builder import ContextBuilder
from .openai_client import OpenAIClient
from .prompt_builder import PromptBuilder


class PatchAgent:
    def __init__(self):

        self.client = OpenAIClient()

        self.prompts = PromptBuilder()

        self.context = ContextBuilder()

    def generate_patch(
        self,
        original_file: str,
    ) -> str:

        source = self.context.file_context(original_file)

        prompt = f"""
Generate a unified git patch.

Requirements:

- Preserve behavior.
- Improve code quality.
- Maximum 600 lines/file.
- Return ONLY the patch.

Code:

{source}
"""

        return self.client.ask(
            prompt=prompt,
            system=self.prompts.system_prompt(),
        )

    def generate_from_review(
        self,
        source: str,
        review: str,
    ) -> str:

        prompt = f"""
Code:

{source}

Review:

{review}

Generate the required patch.
"""

        return self.client.ask(
            prompt=prompt,
            system=self.prompts.system_prompt(),
        )
