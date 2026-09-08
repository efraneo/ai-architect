"""La única llamada al modelo del despachador: el catálogo de comandos elegibles y la pregunta con repliegue de modelos rápidos.

``pide`` reexporta estos nombres."""

from __future__ import annotations

from typing import Any

from ai_architect.commands.pide_guion import (  # noqa: F401 - la API del módulo sigue aquí
    CORTESIA,
    DIAS,
    INSTRUCCIONES,
    MESES,
    _merece_experto,
    _momento,
)
from ai_architect.commands.pide_orden import (  # noqa: F401 - la API del módulo sigue aquí
    BANDERAS_QUE_ESCRIBEN,
    MODIFICAN,
    _argumentos,
    _como_se_escribe,
    _error,
    _leer_json,
)
from ai_architect.commands.pide_respuesta import (  # noqa: F401 - la API del módulo sigue aquí
    _explicar_mejora,
    explicar,
    panel,
)
from ai_architect.core import perfil


def _catalogo() -> tuple[str, dict[str, Any]]:
    """La lista de comandos, tomada de la tabla del CLI.

    Se importa aquí dentro a propósito: el CLI importa este módulo, y hacerlo
    arriba sería un ciclo. Y se toma de allí para que no haya dos listas que
    puedan desincronizarse.
    """
    from ai_architect.cli import COMANDOS

    # Solo lo que responde algo del repositorio. `voz`, `avatar` y
    # `conversar` son la interfaz —abren ventanas, encienden micrófonos— y
    # dejárselos elegir acabó como tenía que acabar: a "saluda a Rafa de mi
    # parte" respondió eligiendo `avatar`, que esperaba un argumento que
    # `pide` no tiene, y reventó con un AttributeError en mitad de la
    # conversación.
    elegibles = [c for c in COMANDOS if c.elegible]

    lineas = [f"  {c.nombre}: {c.ayuda}" for c in elegibles]

    return "\n".join(lineas), {c.nombre: c for c in elegibles}


# El despacho es una clasificacion: de una frase corta, un nombre de la
# lista. No hace falta el modelo grande, y con el se notaba — tres segundos
# mirando una cara callada para decidir entre ocho palabras.
#
# En orden y con repliegue, porque no todas las cuentas tienen todos los
# modelos: `gpt-5-mini` contesta 404 pidiendo verificar la organizacion, y
# ese fallo no puede dejar mudo al arquitecto. El ultimo escalon es el
# modelo por defecto del proveedor, que siempre esta.
MODELOS_RAPIDOS = ("gpt-5-mini", "gpt-4o-mini")


# El primero que funciono. Reintentar los caidos en cada frase seria pagar
# justo la latencia que se venia a quitar.
_modelo_bueno: str | None = None


def _memoria_segura() -> str:
    """Los hechos que Architect sabe del usuario, o nada: la memoria nunca rompe el despacho."""
    try:
        from ai_architect.agente import memoria

        return memoria.para_prompt()
    except Exception:  # noqa: BLE001
        return ""


def _preguntar(engine: Any, catalogo: str, frase: str, repositorio: str = ".") -> str:
    proveedor = engine

    if proveedor is None:
        from ai_architect.providers.provider_manager import ProviderManager

        proveedor = ProviderManager()

    orden = INSTRUCCIONES.format(
        catalogo=catalogo,
        frase=frase,
        trato=perfil.como_llamarte(),
        momento=_momento(),
        repositorio=repositorio,
        memoria=_memoria_segura(),
    )

    # Un motor inyectado en las pruebas no tiene por que aceptar `model`.
    if engine is not None:
        return str(proveedor.generate(orden))

    global _modelo_bueno

    if _modelo_bueno:
        return str(proveedor.generate(orden, model=_modelo_bueno))

    ultimo: Exception | None = None

    for modelo in MODELOS_RAPIDOS:
        try:
            salida = str(proveedor.generate(orden, model=modelo))

        except Exception as e:  # noqa: BLE001 - se prueba el siguiente
            ultimo = e

            continue

        _modelo_bueno = modelo

        return salida

    # Ninguno de los rapidos: se cae al de siempre, que sera mas lento pero
    # contesta. Que tarde es peor que que no funcione.
    try:
        return str(proveedor.generate(orden))

    except Exception as fallo:
        # Se cuenta el fallo del rápido, no el del lento: el primero dice
        # por qué se llegó hasta aquí, que es lo que habría que arreglar.
        raise (ultimo if ultimo is not None else fallo) from fallo
