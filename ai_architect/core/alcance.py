"""
=========================================================
Alcance

Que un parche no escriba fuera de su repositorio.
=========================================================

Un parche dice sobre qué archivos actúa, y esos nombres los escribe un
modelo. ``git apply`` los interpreta relativos al repositorio, y un
``../../`` en la cabecera sube por el árbol tan tranquilo. La ruta absoluta
tampoco cuesta nada de escribir.

Hasta ahora lo único que frenaba eso era el ``--si``, que autoriza a
modificar **el repositorio** — no el disco. Son permisos distintos y se
estaban confundiendo en uno.

**Por qué se comprueba antes y no después.** Un parche se aplica entero o
no se aplica: si git escribe tres archivos y el cuarto está fuera, los tres
primeros ya están escritos. Mirar los nombres antes cuesta un milisegundo
y evita tener que deshacer algo que ya pasó.

Esto no es un antídoto contra un atacante decidido —un enlace simbólico
dentro del repositorio apunta a donde quiera— sino contra el caso real: un
modelo que se equivoca de ruta y un usuario que dijo "sí" a otra cosa.
"""

from __future__ import annotations

import re
from pathlib import Path

# De dónde salen los nombres de archivo en un diff unificado.
DESTINOS = re.compile(r"^\+\+\+ (?:b/)?(.+?)(?:\t.*)?$", re.MULTILINE)

ORIGENES = re.compile(r"^--- (?:a/)?(.+?)(?:\t.*)?$", re.MULTILINE)

# `git apply` usa esto para decir "este archivo no existe", y no es una ruta.
NADA = "/dev/null"


def rutas_del_parche(diff: str) -> list[str]:
    """Todos los archivos que el parche dice tocar, tal como los nombra."""
    nombres = DESTINOS.findall(diff or "") + ORIGENES.findall(diff or "")

    return [n.strip() for n in nombres if n.strip() and n.strip() != NADA]


def se_sale(ruta: str, repositorio: Path) -> bool:
    """Si esa ruta acaba fuera del repositorio.

    Se resuelve contra el repositorio y se compara el resultado, en vez de
    buscar ``..`` en el texto: ``a/../../etc`` y ``a/./../..`` son la misma
    escapada escrita de dos formas, y buscando cadenas se escapan las dos.
    """
    if not ruta:
        return False

    candidata = Path(ruta)

    # Una ruta absoluta ya está fuera por definición, salvo que caiga
    # dentro por casualidad — y eso lo dice la comprobación de abajo.
    entera = candidata if candidata.is_absolute() else repositorio / candidata

    try:
        raiz = repositorio.resolve()
        # `strict=False`: el archivo puede no existir todavía, que es
        # justo el caso de un parche que crea uno nuevo.
        destino = entera.resolve()

    except OSError:
        # Si no se puede resolver, no se aplica. Ante la duda, no.
        return True

    return raiz != destino and raiz not in destino.parents


def revisar(diff: str, repositorio: Path) -> list[str]:
    """Las rutas del parche que se salen. Vacío si todas están dentro."""
    return sorted(
        {ruta for ruta in rutas_del_parche(diff) if se_sale(ruta, repositorio)}
    )


def motivo(fuera: list[str], repositorio: Path) -> str:
    """Qué se le dice al usuario cuando un parche quiere salirse."""
    cuantas = "una ruta" if len(fuera) == 1 else f"{len(fuera)} rutas"

    return (
        f"El parche toca {cuantas} fuera de {repositorio.name}: "
        f"{', '.join(fuera[:4])}. No lo aplico. "
        "Autorizar cambios en un repositorio no es autorizar cambios en el disco."
    )
