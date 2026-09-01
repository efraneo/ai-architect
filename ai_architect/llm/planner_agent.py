"""
=========================================================
Planner Agent
=========================================================
"""

from __future__ import annotations

from .context_builder import ContextBuilder
from .openai_client import OpenAIClient
from .prompt_builder import PromptBuilder


class PlannerAgent:
    def __init__(self):

        self.client = OpenAIClient()

        self.prompts = PromptBuilder()

        self.context = ContextBuilder()

    def create_plan(
        self,
        analysis: dict,
    ) -> str:

        summary = self.context.summary(analysis)

        return self.client.ask(
            prompt=self.prompts.improvement_prompt(summary),
            system=self.prompts.system_prompt(),
        )
