"""
Gemini Provider
"""

from __future__ import annotations

import os
from typing import Any

import google.generativeai as genai

from ai_architect.providers.base_provider import BaseProvider


class GeminiProvider(BaseProvider):
    """
    Google Gemini Provider.
    """

    def __init__(self) -> None:
        super().__init__()

        self.api_key = os.getenv(
            "GOOGLE_API_KEY",
            "",
        )

        self.client: genai.GenerativeModel | None = None

        if self.api_key:
            genai.configure(
                api_key=self.api_key,
            )

            self.client = genai.GenerativeModel(
                self.model,
            )

    def default_model(self) -> str:
        return os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-pro",
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
            raise RuntimeError("GOOGLE_API_KEY is not configured.")

        response = client.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
            },
            **kwargs,
        )

        text = getattr(
            response,
            "text",
            "",
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
            result = client.count_tokens(
                text,
            )

            return int(result.total_tokens)

        except Exception:
            return 0

    def models(
        self,
    ) -> list[str]:
        if not self.available():
            return []

        result: list[str] = []

        for model in genai.list_models():
            name = getattr(
                model,
                "name",
                None,
            )

            if isinstance(name, str):
                result.append(name)

        return result
