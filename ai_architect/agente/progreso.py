"""
=========================================================
Progreso

Lo que Architect va haciendo, contado en vivo.
=========================================================

Hasta ahora ``hacer`` trabajaba en silencio y al final soltaba el informe. Para
el rostro (fase 4) hace falta lo contrario: saber **en el momento** qué
herramienta acaba de arrancar, si terminó bien, y cuándo quiso escribir y se
le negó. Con eso la cara pasa a «trabajando», enseña una tarjeta por
herramienta y se pone en ámbar cuando pide permiso.

Es un tablón de anuncios: quien quiera enterarse se suscribe con una función;
``hacer`` engancha su ``EventBus`` aquí y los avisos salen solos. Un oyente que
falla no puede frenar el trabajo: se ignora.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from ai_architect.agente.eventos import Event, EventBus, EventType

Oyente = Callable[[dict[str, Any]], None]

_oyentes: list[Oyente] = []
_lock = threading.Lock()

# Cuánto se cuenta de los argumentos y del resultado. Es para una tarjeta,
# no para un registro.
RESUMEN = 120


def suscribir(oyente: Oyente) -> None:
    with _lock:
        if oyente not in _oyentes:
            _oyentes.append(oyente)


def desuscribir(oyente: Oyente) -> None:
    with _lock:
        if oyente in _oyentes:
            _oyentes.remove(oyente)


def avisar(tipo: str, **datos: Any) -> dict[str, Any]:
    """Publica un aviso a todos los oyentes y lo devuelve."""
    aviso: dict[str, Any] = {"tipo": tipo, "cuando": time.time(), **datos}

    with _lock:
        oyentes = list(_oyentes)

    for oyente in oyentes:
        try:
            oyente(aviso)

        except Exception:  # noqa: BLE001 - un oyente roto no frena el trabajo
            continue

    return aviso


def enganchar(bus: EventBus) -> None:
    """Que las herramientas de ese bus se cuenten aquí."""

    def inicio(evento: Event) -> None:
        datos = evento.data or {}

        avisar(
            "herramienta_inicio",
            herramienta=str(datos.get("tool", "")),
            argumentos=resumir_argumentos(datos.get("arguments")),
        )

    def fin(evento: Event) -> None:
        datos = evento.data or {}

        avisar(
            "herramienta_fin",
            herramienta=str(datos.get("tool", "")),
            ok=bool(datos.get("success")),
            detalle=" ".join(str(datos.get("result", "")).split())[:RESUMEN],
        )

    bus.subscribe(EventType.TOOL_CALL_START, inicio)
    bus.subscribe(EventType.TOOL_CALL_END, fin)


def resumir_argumentos(argumentos: Any) -> str:
    """Lo más significativo de los argumentos de una herramienta, en una línea."""
    if isinstance(argumentos, dict):
        for clave in ("path", "command", "message", "patch", "query", "task"):
            valor = argumentos.get(clave)

            if valor:
                return " ".join(str(valor).split())[:RESUMEN]

        return ", ".join(str(k) for k in argumentos)[:RESUMEN]

    return " ".join(str(argumentos or "").split())[:RESUMEN]


class Bitacora:
    """Los avisos recibidos, numerados, para que una página los pida «desde el N»."""

    def __init__(self, maximo: int = 400) -> None:
        self._avisos: list[dict[str, Any]] = []
        self._n = 0
        self._maximo = maximo
        self._lock = threading.Lock()

    def anotar(self, aviso: dict[str, Any]) -> None:
        with self._lock:
            self._n += 1
            self._avisos.append({**aviso, "n": self._n})

            if len(self._avisos) > self._maximo:
                del self._avisos[: len(self._avisos) - self._maximo]

    def desde(self, n: int) -> dict[str, Any]:
        with self._lock:
            nuevos = [a for a in self._avisos if a["n"] > n]

            return {"avisos": nuevos, "n": self._n}

    def limpiar(self) -> None:
        with self._lock:
            self._avisos.clear()

    @property
    def ultimo(self) -> int:
        return self._n
