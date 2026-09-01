"""
=========================================================
Provider Factory

Creates the configured LLM provider.
=========================================================
"""

from __future__ import annotations

import os

from ai_architect.providers.base_provider import BaseProvider


class ProviderFactory:
    """
    Lazy factory responsible for creating
    the configured provider.

    Providers are imported only when needed,
    avoiding unnecessary third-party dependencies.
    """

    def __init__(self) -> None:

        self.provider = os.getenv(
            "AI_PROVIDER",
            "openai",
        ).lower()

    ##########################################################

    def create(self) -> BaseProvider:

        provider = self.provider

        if provider == "openai":
            from ai_architect.providers.openai_provider import (
                OpenAIProvider,
            )

            return OpenAIProvider()

        if provider == "claude":
            from ai_architect.providers.claude_provider import (
                ClaudeProvider,
            )

            return ClaudeProvider()

        if provider == "gemini":
            from ai_architect.providers.gemini_provider import (
                GeminiProvider,
            )

            return GeminiProvider()

        if provider == "ollama":
            from ai_architect.providers.ollama_provider import (
                OllamaProvider,
            )

            return OllamaProvider()

        if provider == "openrouter":
            from ai_architect.providers.openrouter_provider import (
                OpenRouterProvider,
            )

            return OpenRouterProvider()

        raise ValueError(f"Unknown provider: {provider}")

    ##########################################################

    @staticmethod
    def available() -> list[str]:

        return [
            "openai",
            "claude",
            "gemini",
            "ollama",
            "openrouter",
        ]

    ##########################################################

    def current(self) -> str:

        return self.provider

    ##########################################################

    def exists(
        self,
        provider: str,
    ) -> bool:

        return provider.lower() in self.available()
