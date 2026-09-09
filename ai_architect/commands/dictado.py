"""
=========================================================
Dictado

«Escribe lo siguiente en Word»: Architect abre Word y escribe lo que le dictes.
=========================================================

Mientras el dictado está activo, cada frase que oye va al documento tal cual,
con los signos dichos con palabras («coma», «punto seguido», «punto y aparte»,
«dos puntos», «abre paréntesis»…). Dentro del dictado se entienden estas órdenes:

    agrega una tabla / inserta una tabla      → pregunta filas y columnas y la mete
    3 filas y 4 columnas (con títulos a, b, c) → responde a esa pregunta
    en la fila 2 columna 3 escribe: X          → llena una celda
    borra eso / deshacer                       → deshace lo último
    guarda el documento (como X)               → .docx en el escritorio
    termina el dictado / deja de escribir      → vuelve a la conversación normal

Las órdenes de Architect que no son texto («cierra Architect», «qué hora es»)
siguen funcionando: el dictado solo se come lo que parece texto.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect.core.texto import sin_adornos

EMPEZAR = (
    "escribe lo siguiente en word",
    "escribe en word",
    "escribe esto en word",
    "escribeme en word",
    "dicta en word",
    "toma nota en word",
    "toma dictado",
    "te voy a dictar",
    "voy a dictarte",
    "abre word y escribe",
    "escribe en un documento",
    "escribe lo siguiente",
    "vamos a escribir en word",
    "empieza el dictado",
    "inicia el dictado",
)

TERMINAR = (
    "termina el dictado",
    "fin del dictado",
    "deja de escribir",
    "para de escribir",
    "ya no escribas",
    "terminamos el dictado",
    "detén el dictado",
    "deten el dictado",
    "listo con el dictado",
    "eso es todo",
)

TABLA = (
    "agrega una tabla",
    "inserta una tabla",
    "pon una tabla",
    "crea una tabla",
    "agregame una tabla",
    "tabla nueva",
)
DESHACER = (
    "borra eso",
    "deshacer",
    "deshace eso",
    "borra lo ultimo",
    "quita eso",
    "borra la ultima frase",
)

# Órdenes de Architect que no son texto dictado: pasan a la conversación normal.
NO_ES_TEXTO = (
    "cierra architect",
    "cerrar",
    "cierra",
    "cierrate",
    "apagate",
    "despidete",
    "adios",
    "que hora es",
    "que dia es",
    "hiberna",
    "descansa",
    "quedate en reposo",
    "maximiza ventana",
    "minimiza ventana",
    "adelante",
)

FILAS_COLUMNAS = re.compile(
    r"(?P<f>\d+)\s*(?:filas?|renglones?)?\s*(?:y|por|x|\*|,)?\s*(?P<c>\d+)\s*(?:columnas?)?"
)
CELDA = re.compile(
    r"^(?:en la\s+)?fila\s+(?P<f>\d+)\s*,?\s*(?:y\s+)?columna\s+(?P<c>\d+)\s*,?\s*(?:escribe|pon|coloca)?\s*:?\s*(?P<t>.+)$"
)
GUARDAR = re.compile(
    r"^guarda(?:lo)?(?:\s+el\s+documento)?(?:\s+(?:como|con el nombre)\s+(?P<n>.+))?$"
)

_estado: dict[str, Any] = {"activo": False, "esperando_tabla": False}


def activo() -> bool:
    return bool(_estado["activo"])


def quiere_empezar(frase: str) -> bool:
    plano = sin_adornos(frase)

    return any(plano.startswith(e) for e in EMPEZAR)


def empezar(frase: str = "") -> dict[str, Any]:
    """Abre Word (o se conecta al abierto) y activa el dictado."""
    from ai_architect.office import word

    if not word.disponible():
        return {
            "respuesta": (
                "Para dictar necesito Microsoft Word en este equipo y el paquete pywin32. "
                "Si Word está, di «instala pywin32» y lo pongo."
            )
        }

    abierto = word.abrir()

    if not abierto.get("ok"):
        return {"respuesta": str(abierto.get("error"))}

    _estado["activo"] = True
    _estado["esperando_tabla"] = False

    # Si la orden ya traía texto («escribe lo siguiente en Word: hola…»), va ya.
    plano = sin_adornos(frase)
    resto = ""

    for e in EMPEZAR:
        if plano.startswith(e):
            resto = frase.strip()[len(frase.strip()) - len(plano) + len(e) :].strip(
                " :,."
            )

            break

    if resto and len(resto.split()) >= 2:
        word.escribir(resto)

        return {
            "respuesta": "Escrito. Sigue dictando; di «termina el dictado» para parar.",
            "dictando": True,
        }

    return {
        "respuesta": (
            "Word listo. Dicta y lo escribo tal cual; di «coma», «punto seguido», «punto y "
            "aparte», «agrega una tabla», «guarda el documento» o «termina el dictado»."
        ),
        "dictando": True,
    }


def terminar() -> dict[str, Any]:
    _estado["activo"] = False
    _estado["esperando_tabla"] = False

    return {"respuesta": "Dictado terminado.", "dictando": False}


def atender(frase: str) -> dict[str, Any] | None:
    """Una frase mientras se dicta. ``None`` si no era para el dictado (sigue el
    camino normal: cerrar, hora, etc.)."""
    if not activo():
        return None

    from ai_architect.office import word

    plano = sin_adornos(frase)

    if not plano:
        return {"respuesta": ""}

    if any(plano == t or plano.startswith(t) for t in TERMINAR):
        return terminar()

    if plano in NO_ES_TEXTO or any(
        plano.startswith(t + " ") for t in ("cierra", "cerrar", "hiberna", "descansa")
    ):
        return None

    if _estado["esperando_tabla"]:
        m = FILAS_COLUMNAS.search(_numeros(plano))

        if m is None:
            return {
                "respuesta": "Dime cuántas filas y cuántas columnas, por ejemplo «3 filas y 4 columnas»."
            }

        encabezados = _encabezados(frase)
        hecho = word.tabla(int(m["f"]), int(m["c"]), encabezados)
        _estado["esperando_tabla"] = False

        if not hecho.get("ok"):
            return {"respuesta": str(hecho.get("error"))}

        return {
            "respuesta": f"Tabla de {hecho['filas']} por {hecho['columnas']} insertada."
            + (" Con los títulos." if encabezados else "")
            + " Sigue dictando."
        }

    if any(plano.startswith(t) for t in TABLA):
        m = FILAS_COLUMNAS.search(_numeros(plano))

        if m is not None:
            hecho = word.tabla(int(m["f"]), int(m["c"]), _encabezados(frase))

            return {
                "respuesta": (
                    f"Tabla de {hecho.get('filas')} por {hecho.get('columnas')} insertada."
                    if hecho.get("ok")
                    else str(hecho.get("error"))
                )
            }

        _estado["esperando_tabla"] = True

        return {"respuesta": "¿Cuántas filas y cuántas columnas?"}

    m = CELDA.match(plano)

    if m is not None:
        texto = frase.strip()[len(frase.strip()) - len(m["t"]) :].strip(" :,.")
        hecho = word.celda(int(m["f"]), int(m["c"]), texto)

        return {"respuesta": "Puesto." if hecho.get("ok") else str(hecho.get("error"))}

    if plano in DESHACER:
        hecho = word.deshacer()

        return {"respuesta": "Borrado." if hecho.get("ok") else str(hecho.get("error"))}

    m = GUARDAR.match(plano)

    if m is not None:
        nombre = m["n"] or ""
        hecho = word.guardar(nombre)

        return {
            "respuesta": (
                f"Guardado en {hecho['ruta']}."
                if hecho.get("ok")
                else str(hecho.get("error"))
            )
        }

    if plano in (
        "punto y aparte",
        "nuevo parrafo",
        "otro parrafo",
        "nueva linea",
        "salto de linea",
    ):
        word.parrafo()

        return {"respuesta": ""}

    hecho = word.escribir(frase)

    if not hecho.get("ok"):
        return {"respuesta": str(hecho.get("error"))}

    # Escrito en silencio: contestar a cada frase sería insoportable.
    return {"respuesta": "", "escrito": hecho.get("escrito", "")}


def _numeros(plano: str) -> str:
    """«tres filas y cuatro columnas» → «3 filas y 4 columnas»."""
    from ai_architect.commands.calcular import NUMEROS

    salida = plano

    for palabra, numero in sorted(NUMEROS.items(), key=lambda p: -len(p[0])):
        salida = re.sub(rf"\b{palabra}\b", str(numero), salida)

    return salida


def _encabezados(frase: str) -> list[str]:
    """«… con los títulos nombre, edad y cargo» → ["nombre", "edad", "cargo"]."""
    m = re.search(
        r"(?:con (?:los )?(?:t[ií]tulos|encabezados|columnas)|titulad[ao]s?)\s*:?\s*(?P<l>.+)$",
        frase,
        re.IGNORECASE,
    )

    if m is None:
        return []

    lista = re.split(r"\s*,\s*|\s+y\s+", m["l"].strip(" ."))

    return [t.strip() for t in lista if t.strip()][:30]
