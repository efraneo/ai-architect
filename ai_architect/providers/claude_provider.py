"""
Claude Provider
"""

from __future__ import annotations

import os
from typing import Any, Literal

import anthropic
from anthropic.types import OutputConfigParam

from ai_architect.providers.base_provider import BaseProvider

# Depth of reasoning, replacing the old `temperature`. Anthropic removed the
# sampling parameters (temperature / top_p / top_k) on the current models, and
# `output_config.effort` is what controls that tradeoff now.
Effort = Literal["low", "medium", "high", "xhigh", "max"]

DEFAULT_EFFORT: Effort = "high"

# The SDK requires streaming for very long outputs so the request does not hit
# the HTTP timeout. 16000 is the recommended ceiling for non-streaming calls.
MAX_TOKENS = 16000


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
            "claude-opus-5",
        )

    def available(self) -> bool:
        return self.client is not None

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        effort: Effort | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text with Claude.

        ``temperature`` stays in the signature because it is part of the
        :class:`BaseProvider` contract and the other providers (OpenAI, Gemini,
        Ollama) do use it. Anthropic **removed** the sampling parameters on the
        current models, so it is not forwarded: it is translated to ``effort``,
        which is what controls the tradeoff now. Pass ``effort`` directly to
        choose the level yourself.
        """
        client = self.client

        if client is None:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured.")

        salida: OutputConfigParam = {
            "effort": effort or self.effort_for(temperature),
        }

        response = client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            output_config=salida,
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

        return self._first_text(response)

    @staticmethod
    def effort_for(temperature: float) -> Effort:
        """Translate a ``temperature`` from the common contract to an effort level.

        The mapping is deliberate, not a conversion: they measure different
        things. A low temperature signals "be precise, do not improvise", and
        the equivalent with Claude is to give it more room to reason. So a low
        temperature maps to a *higher* effort, not a lower one.
        """
        if temperature <= 0.15:
            return "xhigh"

        if temperature <= 0.5:
            return "high"

        return "medium"

    @staticmethod
    def _first_text(response: Any) -> str:
        """Return the first text block of the response.

        ``response.content`` is a list of blocks, and the first one is not
        necessarily the answer: with thinking enabled it is a ``thinking``
        block, and reading ``content[0].text`` would yield an empty string.
        """
        for block in getattr(response, "content", None) or []:
            if getattr(block, "type", None) != "text":
                continue

            text = getattr(block, "text", None)

            if isinstance(text, str):
                return text.strip()

        return ""

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
