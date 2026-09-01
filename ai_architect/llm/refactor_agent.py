"""
=========================================================
Refactor Agent
=========================================================
"""

from __future__ import annotations

from .context_builder import ContextBuilder
from .openai_client import OpenAIClient
from .prompt_builder import PromptBuilder


class RefactorAgent:
    def __init__(self):

        self.client = OpenAIClient()

        self.prompts = PromptBuilder()

        self.context = ContextBuilder()

    def refactor_file(
        self,
        file: str,
    ) -> str:

        source = self.context.file_context(file)

        return self.client.ask(
            prompt=self.prompts.refactor_prompt(source),
            system=self.prompts.system_prompt(),
        )

    def improve_project(
        self,
        files: list[str],
    ) -> str:

        context = self.context.project_context(files)

        return self.client.ask(
            prompt=self.prompts.improvement_prompt(context),
            system=self.prompts.system_prompt(),
        )
