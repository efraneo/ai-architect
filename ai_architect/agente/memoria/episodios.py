"""Memoria episódica: lo que se habló, cuándo.

La memoria de hechos (``memoria.hechos``) guarda lo fijo: «mi café es el
expreso doble». Esta guarda lo que pasó: cada conversación queda en
``conversacion.log`` con fecha y hora, y aquí se busca por día («qué hablamos
el martes») o por tema («qué te dije de las llaves», «dónde dejé las llaves»).

Sin base vectorial: el registro de un asistente personal son unas decenas
de líneas al día, y una búsqueda por palabras con fecha responde en
milisegundos y no se equivoca de martes.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from ai_architect.core.texto import sin_adornos

LINEA = re.compile(
    r"^(?P<fecha>\d{4}-\d{2}-\d{2}) (?P<hora>\d{2}:\d{2}):\d{2}\s+(?P<quien>[<>~·!])\s*(?P<texto>.*)$"
)

DIAS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")

QUE_HABLAMOS = re.compile(
    r"^(?:que hablamos|que conversamos|que te dije|que dije|que me dijiste|que te conte|"
    r"de que hablamos|que paso|recuerdas lo que (?:te )?dije|te acuerdas de lo que (?:te )?dije)"
    r"(?:\s+(?P<resto>.+))?$"
)

DONDE = re.compile(
    r"^(?:donde (?:deje|puse|guarde|quedo|quedaron|estan|esta)|"
    r"que hice con|donde dije que (?:deje|puse|guarde))\s+(?P<que>.+?)\??$"
)

CUANDO = re.compile(
    r"\b(?P<cuando>hoy|ayer|anteayer|antier|el lunes|el martes|el miercoles|el jueves|"
    r"el viernes|el sabado|el domingo|esta semana|la semana pasada|este mes)\b"
)

TEMA = re.compile(r"\b(?:sobre|de|acerca de|del|de la|de las|de los)\s+(?P<tema>.+)$")

PALABRAS_VACIAS = {
    "el",
    "la",
    "los",
    "las",
    "de",
    "del",
    "que",
    "y",
    "a",
    "en",
    "un",
    "una",
    "mi",
    "mis",
    "tu",
    "se",
    "lo",
    "le",
    "me",
    "te",
    "con",
    "por",
    "para",
}


def ruta_registro() -> Path:
    from ai_architect.agente.rutas_agente import get_config_dir

    return Path(get_config_dir()) / "conversacion.log"


def leer(desde: date | None = None, hasta: date | None = None) -> list[dict[str, Any]]:
    """Las líneas del registro entre dos fechas (ambas incluidas)."""
    try:
        lineas = (
            ruta_registro().read_text(encoding="utf-8", errors="replace").splitlines()
        )

    except OSError:
        return []

    salida = []

    for ln in lineas:
        m = LINEA.match(ln)

        if not m:
            continue

        try:
            dia = date.fromisoformat(m.group("fecha"))

        except ValueError:
            continue

        if desde and dia < desde or hasta and dia > hasta:
            continue

        texto = m.group("texto").strip()

        if not texto or m.group("quien") in "~·!":
            continue

        salida.append(
            {
                "fecha": dia,
                "hora": m.group("hora"),
                "quien": (
                    "tú"
                    if m.group("quien") == ">"
                    else "él" if m.group("quien") == "<" else "sistema"
                ),
                "texto": texto,
            }
        )

    return salida


def _rango(cuando: str, hoy: date) -> tuple[date, date]:
    cuando = cuando.strip()

    if cuando == "hoy":
        return hoy, hoy

    if cuando == "ayer":
        return hoy - timedelta(days=1), hoy - timedelta(days=1)

    if cuando in ("anteayer", "antier"):
        return hoy - timedelta(days=2), hoy - timedelta(days=2)

    if cuando == "esta semana":
        return hoy - timedelta(days=hoy.weekday()), hoy

    if cuando == "la semana pasada":
        lunes = hoy - timedelta(days=hoy.weekday() + 7)

        return lunes, lunes + timedelta(days=6)

    if cuando == "este mes":
        return hoy.replace(day=1), hoy

    nombre = cuando.replace("el ", "")

    if nombre in DIAS:
        objetivo = DIAS.index(nombre)
        atras = (hoy.weekday() - objetivo) % 7 or 7

        # «El martes» dicho un martes es el de hoy.
        if hoy.weekday() == objetivo:
            atras = 0

        dia = hoy - timedelta(days=atras)

        return dia, dia

    return hoy - timedelta(days=30), hoy


def _palabras(texto: str) -> list[str]:
    return [
        p
        for p in re.findall(r"[a-záéíóúñ0-9]{3,}", sin_adornos(texto))
        if p not in PALABRAS_VACIAS
    ]


def buscar(
    tema: str = "",
    cuando: str = "",
    hoy: date | None = None,
    solo_tuyo: bool = False,
    maximo: int = 8,
) -> list[dict[str, Any]]:
    hoy = hoy or date.today()
    desde, hasta = _rango(cuando, hoy) if cuando else (hoy - timedelta(days=90), hoy)
    lineas = leer(desde, hasta)
    claves = _palabras(tema)

    if solo_tuyo:
        lineas = [ln for ln in lineas if ln["quien"] == "tú"]

    if claves:
        lineas = [
            ln for ln in lineas if any(c in sin_adornos(ln["texto"]) for c in claves)
        ]

    return lineas[-maximo:]


def _dia_dicho(d: date, hoy: date) -> str:
    if d == hoy:
        return "hoy"

    if d == hoy - timedelta(days=1):
        return "ayer"

    return f"el {DIAS[d.weekday()]} {d.day}"


def en_palabras(lineas: list[dict[str, Any]], hoy: date | None = None) -> str:
    hoy = hoy or date.today()

    if not lineas:
        return "No encuentro nada de eso en lo que hemos hablado."

    partes = []

    for ln in lineas[-5:]:
        texto = ln["texto"]
        texto = re.sub(r"^\(.*?\)\s*", "", texto)[:110]
        partes.append(
            f"{_dia_dicho(ln['fecha'], hoy)} a las {ln['hora']}, {ln['quien']}: {texto}"
        )

    return "; ".join(partes) + "."


def por_voz(frase: str, hoy: date | None = None) -> dict[str, Any] | None:
    """«Qué hablamos el martes», «qué te dije de las llaves», «dónde dejé las llaves»."""
    hoy = hoy or date.today()
    limpia = sin_adornos(frase)

    if not limpia:
        return None

    m = DONDE.match(limpia)

    if m:
        que = m.group("que")
        lineas = buscar(que, "", hoy, solo_tuyo=True)

        if not lineas:
            return {
                "respuesta": f"No me has dicho dónde quedó {que}. Si me lo dices, lo apunto."
            }

        ultima = lineas[-1]

        return {
            "respuesta": f"Me dijiste {_dia_dicho(ultima['fecha'], hoy)} a las {ultima['hora']}: {ultima['texto'][:140]}",
            "panel": {
                "tipo": "texto",
                "titulo": "Lo que dijiste",
                "cuerpo": en_palabras(lineas, hoy),
            },
        }

    m = QUE_HABLAMOS.match(limpia)

    if m is None:
        return None

    resto = m.group("resto") or ""
    c = CUANDO.search(resto)
    cuando = c.group("cuando") if c else ""
    resto_sin_fecha = (
        (resto[: c.start()] + " " + resto[c.end() :]).strip() if c else resto
    )
    t = TEMA.search(resto_sin_fecha)
    tema = t.group("tema") if t else resto_sin_fecha
    solo_tuyo = limpia.startswith(
        ("que te dije", "que dije", "que te conte", "recuerdas lo que", "te acuerdas")
    )
    lineas = buscar(tema, cuando, hoy, solo_tuyo=solo_tuyo)

    return {
        "respuesta": en_palabras(lineas, hoy),
        "panel": {
            "tipo": "texto",
            "titulo": "Lo que hablamos" + (f" {cuando}" if cuando else ""),
            "cuerpo": "\n".join(
                f"{ln['fecha']} {ln['hora']} {ln['quien']}: {ln['texto']}"
                for ln in lineas
            )
            or "nada",
        },
    }
