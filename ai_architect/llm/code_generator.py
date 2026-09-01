"""
=========================================================
Code Generator

LLM-independent Code Generator
=========================================================
"""

from __future__ import annotations

from ai_architect.providers.provider_manager import (
    ProviderManager,
)


class CodeGenerator:
    """
    Generates source code using the configured LLM.

    The generator is provider-agnostic.

    Supported providers are selected through
    ProviderManager.
    """

    SYSTEM_PROMPT = """
You are QUANT AI Architect.

You are a senior software architect.

Rules:

- Return ONLY valid code.
- Do not explain.
- Do not use markdown.
- Preserve project architecture.
- Do not remove existing public APIs.
- Improve readability.
- Keep imports organized.
- Produce production-ready code.
"""

    def __init__(self) -> None:

        self.provider = ProviderManager()

    def generate(
        self,
        instruction: str,
        context: str,
    ) -> str:

        prompt = self.build_prompt(
            instruction,
            context,
        )

        return self.provider.generate(
            prompt,
            temperature=0.15,
        )

    def build_prompt(
        self,
        instruction: str,
        context: str,
    ) -> str:

        return "\n\n".join(
            [
                self.SYSTEM_PROMPT.strip(),
                "TASK",
                instruction,
                "PROJECT CONTEXT",
                context,
                "OUTPUT",
                "Return ONLY the complete updated source code.",
            ]
        )

    def provider_name(
        self,
    ) -> str:

        return self.provider.name

    def model(
        self,
    ) -> str:

        return self.provider.model

    def health(
        self,
    ) -> dict:

        return self.provider.health()

    def configuration(
        self,
    ) -> dict:

        return self.provider.configuration()
