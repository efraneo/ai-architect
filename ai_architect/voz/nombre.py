"""
=========================================================
Nombre

Cuándo lo que se oye va dirigido a Architect.
=========================================================

Un micrófono abierto oye la tele, a quien pasa por detrás y a quien habla por
teléfono al lado. La primera versión exigía que se le llamara por su nombre y
falló por otra cosa: el detector de voz recortaba el arranque de la frase y
«arquitecto» llegaba como «arquitect». Se quitó la palabra clave, y desde
entonces contestaba a todo.

Esto vuelve a ponerla, pero bien:

- **Tolerante al recorte.** «arquitect», «arquitec», «architec» o «arkitecto»
  cuentan como el nombre: se compara por parecido, no por igualdad.
- **Con muletilla delante.** «oye Architect», «hola arquitecto».
- **Al principio o al final.** «Architect, revisa» y «revisa, arquitecto».
- **Con ventana de seguimiento.** Nombrado una vez, durante ``SEGUIMIENTO``
  segundos se le puede seguir hablando sin repetir el nombre; y cada respuesta
  suya reabre la ventana, porque una conversación no se llama por el nombre en
  cada frase.
- **El nombre solo también es algo.** «Architect» a secas es llamarlo: se
  contesta «Dime» y se abre la ventana.

Y el recorte de la primera palabra se arregla en la raíz: el navegador guarda
medio segundo de audio anterior al primer sonido (ver ``rostro.html``).
"""

from __future__ import annotations

import time
from difflib import SequenceMatcher
from typing import NamedTuple

from ai_architect.core.texto import sin_adornos

# Cómo se le llama. Responde a su nombre en inglés y en español; «arquitecta»
# porque el reconocedor a veces cambia la última vocal.
NOMBRES = ("architect", "arquitecto", "arquitecta")

# Lo que suele ir delante del nombre y no es parte de la orden.
MULETILLAS = ("oye", "hey", "ey", "hola", "ok", "okey", "buenas", "eh", "che", "mira")

# Palabras que se parecen al nombre y no lo son. «Revisa la arquitectura» no
# es llamarlo.
NO_ES_EL_NOMBRE = ("arquitectura", "arquitectonico", "arquitectonica", "arquitecturas")

# Cuánto dura la ventana tras nombrarlo o tras contestar. Leer lo que salió
# en pantalla y pensar qué pedir lleva su tiempo.
SEGUIMIENTO = 90.0

# Parecido mínimo con el nombre (0–1). 0,72 acepta «arkitecto» y «architec» y
# rechaza «arquería» o «archivo».
PARECIDO = 0.72

# Un recorte más corto que esto no se puede juzgar: «arq» es cualquier cosa.
MINIMO = 5

MODOS = ("nombre", "libre")


class Decision(NamedTuple):
    """Lo que se decidió sobre una frase oída."""

    para_mi: bool
    orden: str
    nombrado: bool
    solo_nombre: bool


def es_el_nombre(palabra: str) -> bool:
    """Si esa palabra, tal como llegó, es su nombre o un trozo reconocible."""
    plana = sin_adornos(palabra)

    if len(plana) < MINIMO or plana in NO_ES_EL_NOMBRE:
        return False

    for nombre in NOMBRES:
        if nombre.startswith(plana) or plana.startswith(nombre):
            return True

        if SequenceMatcher(None, plana, nombre).ratio() >= PARECIDO:
            return True

    return False


def separar(texto: str) -> tuple[bool, str]:
    """``(lo nombró, lo que queda)``. El nombre se quita; la orden se conserva
    tal como se dijo, con sus mayúsculas y tildes."""
    original = (texto or "").strip()
    palabras = original.split()

    if not palabras:
        return (False, "")

    planas = [sin_adornos(p) for p in palabras]

    # Al principio, con una muletilla delante como mucho.
    desde = 1 if planas[0] in MULETILLAS and len(planas) > 1 else 0

    if es_el_nombre(planas[desde]):
        resto = " ".join(palabras[desde + 1 :]).lstrip(" ,.:;-")

        return (True, resto)

    # Al final: «revisa el proyecto, arquitecto».
    if len(planas) >= 2 and es_el_nombre(planas[-1]):
        resto = " ".join(palabras[:-1]).rstrip(" ,.:;¿?¡!-")

        return (True, resto)

    return (False, original)


def decidir(
    texto: str,
    *,
    modo: str = "libre",
    ultima_vez: float = 0.0,
    ahora: float | None = None,
    seguimiento: float = SEGUIMIENTO,
) -> Decision:
    """Si eso iba para él, y qué queda al quitarle el nombre.

    ``modo`` es ``"nombre"`` (hay que llamarlo, salvo dentro de la ventana) o
    ``"libre"`` (todo lo que se oye va para él). ``ultima_vez`` es cuándo se le
    habló o cuándo terminó de contestar, en el reloj de ``time.monotonic``.
    """
    limpio = (texto or "").strip()

    if not limpio:
        return Decision(False, "", False, False)

    nombrado, resto = separar(limpio)

    if nombrado:
        return Decision(True, resto or limpio, True, not resto)

    if modo != "nombre":
        return Decision(True, limpio, False, False)

    momento = time.monotonic() if ahora is None else ahora

    if ultima_vez and 0 <= momento - ultima_vez <= seguimiento:
        return Decision(True, limpio, False, False)

    return Decision(False, limpio, False, False)
