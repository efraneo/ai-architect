"""
OpenRouter Provider
"""

from __future__ import annotations

import os
from typing import Any, cast

import requests

from ai_architect.providers.base_provider import BaseProvider


class OpenRouterProvider(BaseProvider):
    """
    OpenRouter Provider.

    Compatible with every model exposed by OpenRouter.
    """

    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODELS_URL = "https://openrouter.ai/api/v1/models"

    def __init__(self) -> None:
        super().__init__()

        self.api_key = os.getenv(
            "OPENROUTER_API_KEY",
            "",
        )

        self.site = os.getenv(
            "OPENROUTER_SITE",
            "https://github.com/efraneo/ia_architect",
        )

        self.app_name = os.getenv(
            "OPENROUTER_APP",
            "QUANT AI Architect",
        )

    def default_model(self) -> str:
        return os.getenv(
            "OPENROUTER_MODEL",
            "anthropic/claude-sonnet-4",
        )

    def available(self) -> bool:
        return bool(self.api_key)

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        if not self.available():
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site,
            "X-Title": self.app_name,
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are QUANT AI Architect, "
                        "an autonomous senior software architect."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": temperature,
        }

        payload.update(kwargs)

        response = requests.post(
            self.API_URL,
            headers=headers,
            json=cast(Any, payload),
            timeout=600,
        )

        response.raise_for_status()

        data: Any = response.json()

        if not isinstance(data, dict):
            raise RuntimeError("OpenRouter returned an invalid JSON response.")

        choices = data.get("choices")

        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenRouter response contains no choices.")

        first_choice = choices[0]

        if not isinstance(first_choice, dict):
            raise RuntimeError("OpenRouter returned an invalid choice.")

        message = first_choice.get("message")

        if not isinstance(message, dict):
            raise RuntimeError("OpenRouter response contains no valid message.")

        content = message.get("content")

        if not isinstance(content, str):
            return ""

        return content.strip()

    def models(
        self,
    ) -> list[str]:
        response = requests.get(
            self.MODELS_URL,
            timeout=30,
        )

        response.raise_for_status()

        data: Any = response.json()

        if not isinstance(data, dict):
            return []

        models = data.get(
            "data",
            [],
        )

        if not isinstance(models, list):
            return []

        result: list[str] = []

        for model in models:
            if not isinstance(model, dict):
                continue

            model_id = model.get("id")

            if isinstance(model_id, str):
                result.append(model_id)

        return sorted(result)

    def headers(
        self,
    ) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site,
            "X-Title": self.app_name,
        }

    def configuration(
        self,
    ) -> dict[str, Any]:
        return {
            "provider": "OpenRouter",
            "model": self.model,
            "site": self.site,
            "application": self.app_name,
            "available": self.available(),
        }
