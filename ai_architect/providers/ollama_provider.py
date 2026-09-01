"""
Ollama Provider
"""

from __future__ import annotations

import os
from typing import Any, cast

import requests

from ai_architect.providers.base_provider import BaseProvider


class OllamaProvider(BaseProvider):
    """
    Ollama Local Provider.

    Uses the Ollama REST API.
    """

    def __init__(self) -> None:
        super().__init__()

        self.base_url = os.getenv(
            "OLLAMA_URL",
            "http://localhost:11434",
        ).rstrip("/")

    def default_model(self) -> str:
        return os.getenv(
            "OLLAMA_MODEL",
            "qwen2.5-coder:32b",
        )

    def available(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=3,
            )

            return response.status_code == 200

        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        if not self.available():
            raise RuntimeError("Ollama server is not available.")

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        payload.update(kwargs)

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=cast(Any, payload),
            timeout=600,
        )

        response.raise_for_status()

        data: Any = response.json()

        if not isinstance(data, dict):
            return ""

        content = data.get(
            "response",
            "",
        )

        if not isinstance(content, str):
            return ""

        return content.strip()

    def list_models(
        self,
    ) -> list[str]:
        if not self.available():
            return []

        response = requests.get(
            f"{self.base_url}/api/tags",
            timeout=10,
        )

        response.raise_for_status()

        data: Any = response.json()

        if not isinstance(data, dict):
            return []

        models = data.get(
            "models",
            [],
        )

        if not isinstance(models, list):
            return []

        result: list[str] = []

        for model in models:
            if not isinstance(model, dict):
                continue

            name = model.get("name")

            if isinstance(name, str):
                result.append(name)

        return sorted(result)

    def pull(
        self,
        model: str,
    ) -> bool:
        response = requests.post(
            f"{self.base_url}/api/pull",
            json={
                "name": model,
            },
            timeout=None,
        )

        return response.status_code == 200

    def embeddings(
        self,
        text: str,
    ) -> list[float]:
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text,
            },
            timeout=300,
        )

        response.raise_for_status()

        data: Any = response.json()

        if not isinstance(data, dict):
            return []

        embedding = data.get(
            "embedding",
            [],
        )

        if not isinstance(embedding, list):
            return []

        result: list[float] = []

        for value in embedding:
            if isinstance(value, (int, float)):
                result.append(float(value))

        return result
