"""
=========================================================
Task Dispatcher

Corre varios agentes a la vez.
=========================================================

**Dónde ayuda y dónde no.** Se midió sobre este repositorio:

- Los once agentes **estáticos** con hilos: 2,14x más **lento**. Su trabajo
  no está repartido, está repetido -- cada uno recorría el mismo árbol. Lo
  que ahí funciona es compartir el recorrido (``agents/scope.py``), no
  multiplicar los hilos.
- Los cinco agentes de **IA**: 5x más rápido. Ahí el tiempo se va esperando
  al proveedor, y esperar cinco veces a la vez cuesta lo mismo que esperar
  una.

Por eso esto solo se usa para la mitad de IA.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

MAX_HILOS = 8


class TaskDispatcher:
    def dispatch(
        self,
        agents: list[Any],
        trabajo: Callable[[Any], Any],
        *,
        nombre: Callable[[Any], str] | None = None,
    ) -> dict[str, Any]:
        """Ejecuta ``trabajo(agente)`` para cada agente, a la vez.

        Un agente que revienta no tumba a los demás: su casilla lleva el
        error y el resto reporta igual.

        Parameters
        ----------
        agents:
            Los agentes a ejecutar.
        trabajo:
            Qué hacer con cada uno. Los estáticos exponen ``review(ruta)`` y
            los de IA ``run(contexto)``: qué se llama lo decide quien
            despacha, no este módulo.
        nombre:
            Cómo nombrar cada casilla del informe. Por defecto, ``agent.name``.
        """
        if not agents:
            # ThreadPoolExecutor(max_workers=0) revienta con ValueError.
            return {}

        etiqueta = nombre or (lambda agente: str(getattr(agente, "name", agente)))

        reports: dict[str, Any] = {}

        with ThreadPoolExecutor(max_workers=min(len(agents), MAX_HILOS)) as executor:
            futuros = {executor.submit(trabajo, agente): agente for agente in agents}

            for futuro in as_completed(futuros):
                agente = futuros[futuro]

                try:
                    reports[etiqueta(agente)] = futuro.result()

                except Exception as error:  # noqa: BLE001 - uno no tumba al resto
                    reports[etiqueta(agente)] = {
                        "status": "error",
                        "error": str(error),
                    }

        return reports
