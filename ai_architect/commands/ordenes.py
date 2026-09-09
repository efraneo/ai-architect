"""
=========================================================
Órdenes

Separar una frase con varias órdenes en sus partes, en orden.
=========================================================

«Guárdalo en Word y ponlo en el escritorio», «revisa el proyecto y luego
cierra la ventana», «llama a Juan; después bloquea el celular». Hasta ahora
la frase entera iba al modelo como una sola cosa y la mitad se perdía.

La regla es conservadora: se corta por los conectores de secuencia («luego»,
«después», «entonces», «también», «además», «;») y por « y » **solo cuando lo
que sigue empieza por un verbo en imperativo** de los que se le dicen a
Architect. «Revisa el proyecto y dime qué tal está» no se corta: «dime» es
continuación, no otra orden.
"""

from __future__ import annotations

import re

from ai_architect.core.texto import sin_adornos

MAXIMO_PARTES = 4

# Conectores que separan órdenes casi siempre.
SECUENCIA = re.compile(
    r"\s*(?:[,;]\s*)?\b(?:y luego|luego|y despues|despues|y después|después|"
    r"y entonces|entonces|y tambien|y también|tambien|también|y ademas|además|ademas)\b\s*(?:de eso\s*)?",
    re.IGNORECASE,
)

# Verbos con los que empieza una orden nueva tras « y ».
IMPERATIVOS = (
    "revisa",
    "analiza",
    "pasalo",
    "pasala",
    "guardalo",
    "guardala",
    "guarda",
    "ponlo",
    "ponla",
    "pon",
    "abre",
    "cierra",
    "llama",
    "bloquea",
    "manda",
    "envia",
    "crea",
    "graba",
    "muestra",
    "corre",
    "ejecuta",
    "mejora",
    "arregla",
    "corrige",
    "instala",
    "descarga",
    "busca",
    "lee",
    "escribe",
    "recuerda",
    "olvida",
    "pausa",
    "cuelga",
    "reproduce",
    "apaga",
    "enciende",
    "amplia",
    "ampliala",
    "reduce",
    "reducela",
    "quedate",
    "transformate",
    "haz",
    "hazme",
    "prepara",
    "genera",
    "calcula",
    "cuenta",
    "conectate",
    "configura",
    "reparate",
    "sube",
    "baja",
    "borra",
    "elimina",
    "mueve",
    "copia",
    "aplica",
    "prueba",
    "comprueba",
    "mira",
    "termina",
    "para",
    "detente",
    "sigue",
    "repite",
    "vuelve",
    "duerme",
    "descansa",
)

_Y = re.compile(r"\s+y\s+", re.IGNORECASE)


def _empieza_con_imperativo(trozo: str) -> bool:
    palabras = sin_adornos(trozo).split()

    return bool(palabras) and palabras[0] in IMPERATIVOS


def _partir_por_y(texto: str) -> list[str]:
    partes: list[str] = []
    resto = texto

    while True:
        m = _Y.search(resto)

        if m is None:
            partes.append(resto)

            break

        despues = resto[m.end() :]

        if (
            _empieza_con_imperativo(despues)
            and len(sin_adornos(resto[: m.start()]).split()) >= 2
        ):
            partes.append(resto[: m.start()])
            resto = despues

        else:
            # Ese « y » une, no separa: se busca el siguiente.
            siguiente = _Y.search(resto, m.end())

            if siguiente is None:
                partes.append(resto)

                break

            # se reintenta desde el siguiente « y » sin perder el trozo
            cabeza = resto[: siguiente.start()]
            cola = resto[siguiente.end() :]

            if _empieza_con_imperativo(cola):
                partes.append(cabeza)
                resto = cola

            else:
                partes.append(resto)

                break

    return partes


def separar(frase: str) -> list[str]:
    """Las órdenes de la frase, en orden. Una sola si no hay nada que separar."""
    texto = " ".join((frase or "").split())

    if not texto:
        return []

    # Las comillas son sagradas: lo de dentro no se corta.
    if texto.count('"') >= 2 or texto.count("«") >= 1:
        return [texto]

    trozos: list[str] = []

    for parte in SECUENCIA.split(texto):
        for sub in _partir_por_y(parte):
            limpio = sub.strip(" ,;.")

            if len(sin_adornos(limpio).split()) >= 1:
                trozos.append(limpio)

    trozos = [t for t in trozos if t]

    if len(trozos) <= 1:
        return [texto]

    return trozos[:MAXIMO_PARTES]
