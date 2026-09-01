"""
=========================================================
Reviewer Agent
=========================================================
"""

from __future__ import annotations

from .context_builder import ContextBuilder
from .openai_client import OpenAIClient
from .prompt_builder import PromptBuilder


class ReviewerAgent:
    def __init__(self):

        self.client = OpenAIClient()

        self.prompts = PromptBuilder()

        self.context = ContextBuilder()

    def review_file(
        self,
        file: str,
    ) -> str:

        code = self.context.file_context(file)

        return self.client.ask(
            prompt=self.prompts.code_review_prompt(code),
            system=self.prompts.system_prompt(),
        )

    def review_project(
        self,
        files: list[str],
    ) -> list[str]:

        reports = []

        for file in files:
            reports.append(self.review_file(file))

        return reports
