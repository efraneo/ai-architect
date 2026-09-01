"""
Claude Provider
"""

from __future__ import annotations

import os
from typing import Any

import anthropic

from ai_architect.providers.base_provider import BaseProvider


class ClaudeProvider(BaseProvider):
    """
    Anthropic Claude Provider.
    """

    def __init__(self) -> None:
        super().__init__()

        self.api_key = os.getenv(
            "ANTHROPIC_API_KEY",
            "",
        )

        self.client: anthropic.Anthropic | None = (
            anthropic.Anthropic(
                api_key=self.api_key,
            )
            if self.api_key
            else None
        )

    def default_model(self) -> str:
        return os.getenv(
            "CLAUDE_MODEL",
            "claude-sonnet-4",
        )

    def available(self) -> bool:
        return self.client is not None

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        client = self.client

        if client is None:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured.")

        response = client.messages.create(
            model=self.model,
            max_tokens=8192,
            temperature=temperature,
            system=(
                "You are QUANT AI Architect, an autonomous senior software engineer."
            ),
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            **kwargs,
        )

        if not response.content:
            return ""

        first_block = response.content[0]

        text = getattr(
            first_block,
            "text",
            None,
        )

        if not isinstance(text, str):
            return ""

        return text.strip()

    def count_tokens(
        self,
        text: str,
    ) -> int:
        client = self.client

        if client is None:
            return 0

        try:
            response = client.messages.count_tokens(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": text,
                    }
                ],
            )

            return int(response.input_tokens)

        except Exception:
            return 0
