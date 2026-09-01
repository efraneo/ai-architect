"""
=========================================================
Base Provider

Abstract Base Class for all LLM Providers
=========================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """
    Abstract interface implemented by every LLM provider.

    Supported providers:

        - OpenAI
        - Claude
        - Gemini
        - Ollama
        - OpenRouter
    """

    def __init__(self) -> None:

        self.model = self.default_model()

    @abstractmethod
    def default_model(self) -> str:
        """
        Returns the provider default model.
        """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        """
        Generates text from a prompt.
        """

    @abstractmethod
    def available(self) -> bool:
        """
        Returns whether the provider is correctly configured.
        """

    @property
    def name(self) -> str:

        return self.__class__.__name__

    def configuration(self) -> dict:

        return {
            "provider": self.name,
            "model": self.model,
            "available": self.available(),
        }

    def health(self) -> dict:

        return {
            "provider": self.name,
            "status": ("ready" if self.available() else "not_configured"),
            "model": self.model,
        }

    def __repr__(self) -> str:

        return f"{self.name}(model={self.model!r})"
