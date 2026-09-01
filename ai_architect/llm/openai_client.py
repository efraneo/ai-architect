"""
=========================================================
OpenAI Client
=========================================================
"""

from __future__ import annotations

import os

from openai import OpenAI


class OpenAIClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-5.5",
    ):

        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

        self.model = model

    def ask(
        self,
        prompt: str,
        system: str,
    ) -> str:

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return response.output_text
