"""
=========================================================
Verification

Aplicar el cambio, ejecutarlo, y deshacerlo si empeora.
=========================================================

El fallo que esto arregla, comprobado sobre un proyecto de juguete:

    un parche que rompe suma(2,2) de 4 a 0
    -> tests_ok que recibió la decisión: True

Las pruebas se ejecutaban **antes** de aplicar el parche, así que
``tests_ok`` significaba "el repositorio estaba en verde", no "el cambio es
bueno". El motor de decisión aprobaba o rechazaba con información sobre un
código que no era el que iba a quedar.

El ciclo era *ejecutar -> modificar*. Aquí es *modificar -> ejecutar ->
deshacer si empeora*, que es lo que hace falta para que el arquitecto pueda
corregirse solo.

**Nada de esto ocurre si no se pide.** Aplicar un parche toca el árbol de
trabajo del usuario, y eso no se hace por defecto.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.execution.git_apply import aplicar


def peor_que(despues: dict[str, Any], antes: dict[str, Any]) -> bool:
    """¿El cambio dejó las pruebas peor de como estaban?

    No basta con "ahora fallan": un repositorio que ya fallaba antes no se
    puede usar para juzgar el parche. Lo que condena a un cambio es romper
    algo que funcionaba, o aumentar el número de fallos.
    """
    if not antes.get("executed") or not despues.get("executed"):
        return False

    if antes.get("success") and not despues.get("success"):
        return True

    return int(despues.get("failed", 0)) > int(antes.get("failed", 0))


def verificar(
    repository: Path,
    diff: str,
    antes: dict[str, Any],
    ejecutar_pruebas,
) -> dict[str, Any]:
    """Aplica el parche, vuelve a ejecutar las pruebas y decide qué hacer.

    Parameters
    ----------
    repository:
        El repositorio sobre el que se trabaja.
    diff:
        El parche generado.
    antes:
        Cómo estaban las pruebas antes de tocar nada. Sirve de referencia:
        un repositorio que ya venía en rojo no condena al parche.
    ejecutar_pruebas:
        Cómo correr la suite. Se inyecta para que las pruebas de este
        proyecto no lancen un pytest dentro de otro.

    Returns
    -------
    dict
        Qué se hizo y cómo quedó. ``tests`` es el resultado **después** del
        cambio cuando se llegó a aplicar; si no, el de antes.
    """
    if not diff.strip():
        return _sin_aplicar(antes, "el parche está vacío")

    aplicado = aplicar(repository, diff)

    if not aplicado["success"]:
        return _sin_aplicar(antes, aplicado["message"])

    despues = ejecutar_pruebas(repository)

    if not peor_que(despues, antes):
        return {
            "applied": True,
            "reverted": False,
            "reason": "el cambio no empeora las pruebas",
            "tests_before": antes,
            "tests": despues,
        }

    # El cambio rompe algo: se deshace. Dejarlo puesto sería lo peor de los
    # dos mundos —el repositorio del usuario roto y el parche igualmente
    # rechazado— y quien pidió la mejora no tiene por qué limpiar detrás.
    deshecho = aplicar(repository, diff, reverse=True)

    return {
        "applied": True,
        "reverted": bool(deshecho["success"]),
        "reason": (
            "el cambio rompe las pruebas: deshecho"
            if deshecho["success"]
            else "el cambio rompe las pruebas y NO se pudo deshacer: "
            f"{deshecho['message']}"
        ),
        "tests_before": antes,
        "tests": despues,
    }


def estado_del_arbol(verificacion: dict[str, Any] | None) -> str:
    """En qué quedaron los archivos del usuario. Es lo primero que quiere
    saber quien ejecuta esto sobre su propio repositorio.

    - ``untouched``: no se aplicó nada, el repositorio está como estaba.
    - ``restored``: se aplicó, rompía las pruebas y se deshizo.
    - ``modified``: se aplicó y **sigue puesto**. Hay que revisarlo.
    - ``dirty``: se aplicó, había que deshacerlo y no se pudo. Lo peor, y
      por eso tiene nombre propio en vez de confundirse con `modified`.
    """
    if verificacion is None or not verificacion["applied"]:
        return "untouched"

    if verificacion["reverted"]:
        return "restored"

    # Si hubo que deshacerlo y no se pudo, el árbol quedó tocado con un
    # cambio que rompe las pruebas: eso no es lo mismo que un cambio bueno
    # esperando revisión.
    if "rompe" in str(verificacion.get("reason", "")):
        return "dirty"

    return "modified"


def _sin_aplicar(antes: dict[str, Any], motivo: str) -> dict[str, Any]:
    """No se llegó a tocar nada: las pruebas siguen siendo las de antes."""
    return {
        "applied": False,
        "reverted": False,
        "reason": motivo,
        "tests_before": antes,
        "tests": antes,
    }
