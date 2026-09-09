"""Proactividad: hablar sin que le pregunten, cuando hay motivo.

Un asistente que solo responde es un buscador con voz. Este latido corre
cada minuto en la conversación (hilo de ``conversar``) y junta los avisos
que toca dar: un recordatorio que vence, lluvia en camino, un correo que
parece urgente, la CI rota. Cada disparador es una función que devuelve
frases; las que cuestan (red) se espacian solas para no repetirse.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

Disparador = Callable[[datetime], list[str]]

# Cada cuánto, como mínimo, se vuelve a mirar cada cosa (segundos).
ESPACIO = {"lluvia": 2 * 3600, "correo": 10 * 60, "ci": 15 * 60}

_ultima_vez: dict[str, float] = {}
_ultimo_dicho: dict[str, str] = {}
_desactivados: set[str] = set()


def _toca(clave: str) -> bool:
    ahora = time.monotonic()

    if ahora - _ultima_vez.get(clave, -1e9) < ESPACIO.get(clave, 0):
        return False

    _ultima_vez[clave] = ahora

    return True


def _sin_repetir(clave: str, texto: str) -> list[str]:
    """Un aviso igual al anterior no se repite (la lluvia no cambia cada dos horas)."""
    if not texto or _ultimo_dicho.get(clave) == texto:
        return []

    _ultimo_dicho[clave] = texto

    return [texto]


# --- disparadores -----------------------------------------------------------------------


def agenda(ahora: datetime) -> list[str]:
    from ai_architect import agenda as agenda_
    from ai_architect.core import perfil

    trato = perfil.como_llamarte()

    return [f"{trato}, te recuerdo: {a['texto']}." for a in agenda_.vencidos(ahora)]


def lluvia(ahora: datetime) -> list[str]:
    if not _toca("lluvia"):
        return []

    from ai_architect import investigar

    return _sin_repetir("lluvia", investigar.alerta_de_lluvia())


def correo(ahora: datetime) -> list[str]:
    if not _toca("correo"):
        return []

    from ai_architect import investigar
    from ai_architect.canales import correo as correo_

    if not correo_.puede_leer():
        return []

    return _sin_repetir("correo", investigar.aviso_de_correo())


def ci(ahora: datetime) -> list[str]:
    if not _toca("ci"):
        return []

    from ai_architect import autoreparacion
    from ai_architect.agents import ordenes

    fuente = autoreparacion.fuente()

    if fuente is None:
        return []

    vista = ordenes.ejecutar("devops", "ver_ci", str(fuente))
    corridas = vista.get("corridas") or []

    if not corridas:
        return []

    ultima = corridas[0]

    if ultima.get("estado") == "failure":
        return _sin_repetir(
            "ci", f"La CI de Architect falló: {ultima.get('titulo', '')}."
        )

    _ultimo_dicho.pop("ci", None)

    return []


DISPARADORES: dict[str, Disparador] = {
    "agenda": agenda,
    "lluvia": lluvia,
    "correo": correo,
    "ci": ci,
}


def desactivar(clave: str) -> None:
    _desactivados.add(clave)


def activar(clave: str) -> None:
    _desactivados.discard(clave)


def latido(ahora: datetime | None = None) -> list[str]:
    """Todo lo que toca decir ahora. Un disparador roto no calla a los demás."""
    ahora = ahora or datetime.now()
    avisos: list[str] = []

    for clave, disparador in DISPARADORES.items():
        if clave in _desactivados:
            continue

        try:
            avisos.extend(disparador(ahora))

        except Exception:  # noqa: BLE001 - se sigue con el siguiente
            continue

    return avisos


def reiniciar() -> None:
    """Para las pruebas: sin espacios ni memoria de lo dicho."""
    _ultima_vez.clear()
    _ultimo_dicho.clear()
    _desactivados.clear()


def estado() -> dict[str, Any]:
    return {
        "disparadores": sorted(DISPARADORES),
        "desactivados": sorted(_desactivados),
        "ultimo_dicho": dict(_ultimo_dicho),
    }
