"""
=========================================================
Provider Manager

Unified LLM Provider Manager
=========================================================
"""

from __future__ import annotations

from typing import Any

from ai_architect.providers.base_provider import (
    BaseProvider,
)
from ai_architect.providers.provider_factory import (
    ProviderFactory,
)


class ProviderManager:
    """
    High-level interface for all LLM providers.

    This is the only class that should be used by the
    rest of QUANT AI Architect.
    """

    def __init__(self) -> None:

        self.factory = ProviderFactory()

        self.provider: BaseProvider = self.factory.create()

    @property
    def name(self) -> str:

        return self.provider.name

    @property
    def model(self) -> str:

        return self.provider.model

    def available(self) -> bool:

        return self.provider.available()

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:

        # Antes de llamar, no despues: comprobarlo despues seria contar el
        # dinero que ya se fue.
        from ai_architect.core import gasto

        puede, motivo = gasto.permitido()

        if not puede:
            raise gasto.TopeAlcanzado(motivo)

        salida = self.provider.generate(
            prompt,
            temperature=temperature,
            **kwargs,
        )

        gasto.registrar(
            str(kwargs.get("model") or getattr(self.provider, "model", "")),
            prompt,
            salida,
        )

        return salida

    def configuration(self) -> dict:

        return self.provider.configuration()

    def health(self) -> dict:

        return self.provider.health()

    def reload(self) -> None:

        self.provider = self.factory.create()

    def switch(
        self,
        provider: str,
    ) -> bool:

        if not self.factory.exists(
            provider,
        ):
            return False

        self.factory.provider = provider.lower()

        self.reload()

        return True

    def providers(self) -> list[str]:

        return self.factory.available()

    def summary(self) -> dict:

        return {
            "provider": self.name,
            "model": self.model,
            "available": self.available(),
            "supported": self.providers(),
        }
