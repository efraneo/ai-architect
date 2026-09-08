"""Registros de agentes y herramientas.

OpenJarvis descubre agentes y tools por decorador. Aquí el catálogo es explícito
(`ai_architect.agente.caja` arma las herramientas que se le dan al agente), así que
los decoradores solo apuntan el nombre y devuelven la clase intacta.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class _Registro:
    def __init__(self, que: str) -> None:
        self.que = que
        self.registrados: dict[str, Any] = {}

    def register(self, nombre: str) -> Callable[[T], T]:
        def decorador(clase: T) -> T:
            self.registrados[nombre] = clase
            return clase

        return decorador

    def get(self, nombre: str) -> Any:
        return self.registrados[nombre]

    def list(self) -> list[str]:
        return sorted(self.registrados)


AgentRegistry = _Registro("agentes")
ToolRegistry = _Registro("herramientas")
EngineRegistry = _Registro("motores")
