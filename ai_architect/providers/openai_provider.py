"""
OpenAI Provider
"""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from ai_architect.providers.base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    """
    OpenAI Provider implementation.
    """

    def __init__(self) -> None:
        super().__init__()

        self.api_key = os.getenv(
            "OPENAI_API_KEY",
            "",
        )

        self.client: OpenAI | None = (
            OpenAI(
                api_key=self.api_key,
            )
            if self.api_key
            else None
        )

    def default_model(self) -> str:
        return os.getenv(
            "OPENAI_MODEL",
            "gpt-5.5",
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
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        request: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are QUANT AI Architect, "
                        "an autonomous senior software "
                        "engineer."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        model_name = self.model.lower()

        if not model_name.startswith("gpt-5"):
            request["temperature"] = temperature

        request.update(kwargs)

        response = client.chat.completions.create(
            **request,
        )

        if not response.choices:
            return ""

        content = response.choices[0].message.content

        if not isinstance(content, str):
            return ""

        return content.strip()

    def list_models(
        self,
    ) -> list[str]:
        client = self.client

        if client is None:
            return []

        models = client.models.list()

        return sorted(model.id for model in models.data)

    def embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small",
    ) -> list[float]:
        client = self.client

        if client is None:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        response = client.embeddings.create(
            model=model,
            input=text,
        )

        if not response.data:
            return []

        return [float(value) for value in response.data[0].embedding]
