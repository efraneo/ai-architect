"""Investigación y noticias: clima, titulares y correo urgente, sin claves.

El agente que mira fuera. Clima con Open-Meteo (gratis, sin clave), noticias
con el RSS de Google News (gratis, sin clave) y correos urgentes con el IMAP
que ya está configurado en ``canales.correo``. El tráfico en vivo necesita
una clave de Google Maps que no hay: se dice, no se inventa.

La ciudad sale de ``ARCHITECT_CIUDAD`` o de la memoria de hechos («vivo en
Bogotá»); si no está, se pregunta y se apunta.
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

from ai_architect.core.texto import contiene, sin_adornos

TIEMPO = 12

GEOCODIFICAR = (
    "https://geocoding-api.open-meteo.com/v1/search?name={ciudad}&count=1&language=es"
)
PRONOSTICO = (
    "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
    "&current=temperature_2m,precipitation,weather_code,wind_speed_10m"
    "&hourly=precipitation_probability&forecast_days=1&timezone=auto"
)
NOTICIAS = "https://news.google.com/rss/search?q={tema}&hl=es-419&gl=CO&ceid=CO:es-419"
PORTADA = "https://news.google.com/rss?hl=es-419&gl=CO&ceid=CO:es-419"

CODIGOS = {
    0: "despejado",
    1: "casi despejado",
    2: "parcialmente nublado",
    3: "nublado",
    45: "con niebla",
    48: "con niebla",
    51: "con llovizna",
    53: "con llovizna",
    55: "con llovizna fuerte",
    61: "con lluvia ligera",
    63: "con lluvia",
    65: "con lluvia fuerte",
    71: "con nieve",
    73: "con nieve",
    75: "con nieve fuerte",
    80: "con chubascos",
    81: "con chubascos",
    82: "con chubascos fuertes",
    95: "con tormenta",
    96: "con tormenta y granizo",
    99: "con tormenta y granizo",
}

CLIMA = (
    "que clima hace",
    "que clima hay",
    "como esta el clima",
    "como esta el tiempo",
    "que tiempo hace",
    "va a llover",
    "lloverá",
    "llovera",
    "esta lloviendo",
    "cuantos grados hay",
    "que temperatura hace",
    "que temperatura hay",
    "el clima",
    "el pronostico",
    "pronostico del tiempo",
)

NOTICIAS_PIDE = re.compile(
    r"^(?:noticias|novedades|titulares|que hay de nuevo|que se dice|que paso)"
    r"(?:\s+(?:de|sobre|en|del|de la|de las|de los)\s+(?P<tema>.+))?$"
)

CORREOS = (
    "tengo correos nuevos",
    "tengo correo nuevo",
    "hay correos nuevos",
    "hay correo nuevo",
    "correos urgentes",
    "algun correo urgente",
    "que correos tengo",
    "revisa mi correo",
    "revisa el correo",
    "lee mi correo",
    "lee el correo",
)

TRAFICO = (
    "como esta el trafico",
    "hay trafico",
    "el trafico",
    "cuanto tardo en llegar",
)

URGENTE = ("urgente", "urgent", "importante", "inmediato", "hoy mismo", "asap", "vence")


# --- red ------------------------------------------------------------------------------


def _obtener(url: str) -> bytes:
    peticion = urllib.request.Request(url, headers={"User-Agent": "Architect/1.0"})

    with urllib.request.urlopen(
        peticion, timeout=TIEMPO
    ) as r:  # noqa: S310 - https fijas
        return bytes(r.read())


def _json(url: str) -> Any:
    return json.loads(_obtener(url).decode("utf-8", errors="replace"))


# --- la ciudad -----------------------------------------------------------------------------


def ciudad() -> str:
    fija = os.environ.get("ARCHITECT_CIUDAD", "").strip()

    if fija:
        return fija

    try:
        from ai_architect.agente import memoria

        for h in memoria.hechos():
            m = re.search(
                r"\b(?:vivo|vive|estoy|esta|estamos)\s+en\s+([A-Za-zÁÉÍÓÚÑáéíóúñ .'-]{3,40})",
                h.text,
            )

            if m:
                return m.group(1).strip(" .")

    except Exception:  # noqa: BLE001 - sin memoria no hay ciudad
        pass

    return ""


def _ciudad_en(limpia: str) -> str:
    m = re.search(r"\b(?:en|de)\s+(?P<c>[a-záéíóúñ][a-záéíóúñ ]{2,30})$", limpia)

    return m.group("c").strip() if m else ""


# --- clima ------------------------------------------------------------------------------------


def clima(lugar: str = "") -> dict[str, Any]:
    lugar = lugar or ciudad()

    if not lugar:
        return {"ok": False, "falta": "ciudad"}

    try:
        geo = _json(GEOCODIFICAR.format(ciudad=urllib.parse.quote(lugar)))
        sitios = geo.get("results") or []

        if not sitios:
            return {"ok": False, "error": f"no encontré «{lugar}»"}

        sitio = sitios[0]
        datos = _json(PRONOSTICO.format(lat=sitio["latitude"], lon=sitio["longitude"]))

    except Exception as e:  # noqa: BLE001 - sin red se dice
        return {"ok": False, "error": f"no pude consultar el clima: {e}"}

    actual = datos.get("current") or {}
    horas = datos.get("hourly") or {}
    probabilidades = horas.get("precipitation_probability") or []
    tiempos = horas.get("time") or []
    ahora = datetime.now()
    proximas = []

    for t, p in zip(tiempos, probabilidades, strict=False):
        try:
            momento = datetime.fromisoformat(t)

        except ValueError:
            continue

        if -3600 <= (momento - ahora).total_seconds() <= 3 * 3600 and p is not None:
            proximas.append(int(p))

    codigo = int(actual.get("weather_code") or 0)

    return {
        "ok": True,
        "ciudad": str(sitio.get("name", lugar)),
        "pais": str(sitio.get("country", "")),
        "temperatura": actual.get("temperature_2m"),
        "estado": CODIGOS.get(codigo, "variable"),
        "lluvia_ahora": float(actual.get("precipitation") or 0) > 0,
        "viento": actual.get("wind_speed_10m"),
        "probabilidad_lluvia_3h": max(proximas) if proximas else None,
    }


def clima_en_palabras(datos: dict[str, Any]) -> str:
    if not datos.get("ok"):
        if datos.get("falta") == "ciudad":
            return (
                "No sé en qué ciudad estás. Dime «recuerda que vivo en …» y te lo digo."
            )

        return str(datos.get("error", "No pude consultar el clima."))

    texto = (
        f"En {datos['ciudad']} hay {datos['temperatura']:.0f} grados, {datos['estado']}"
    )
    prob = datos.get("probabilidad_lluvia_3h")

    if datos.get("lluvia_ahora"):
        texto += ". Está lloviendo ahora"

    elif prob is not None and prob >= 50:
        texto += f". Hay un {prob} % de lluvia en las próximas tres horas"

    elif prob is not None:
        texto += ". No se espera lluvia en las próximas horas"

    return texto + "."


# --- noticias ------------------------------------------------------------------------------


def noticias(tema: str = "", cuantas: int = 5) -> dict[str, Any]:
    url = NOTICIAS.format(tema=urllib.parse.quote(tema)) if tema else PORTADA

    try:
        raiz = ET.fromstring(_obtener(url))

    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"no pude leer las noticias: {e}"}

    titulares = []

    for item in raiz.iter("item"):
        titulo = (item.findtext("title") or "").strip()
        fuente = (item.findtext("source") or "").strip()

        if titulo:
            titulares.append({"titulo": titulo, "fuente": fuente})

        if len(titulares) >= cuantas:
            break

    return {"ok": True, "tema": tema, "titulares": titulares}


def noticias_en_palabras(datos: dict[str, Any]) -> str:
    if not datos.get("ok"):
        return str(datos.get("error"))

    if not datos.get("titulares"):
        return (
            "No encontré titulares"
            + (f" sobre {datos['tema']}" if datos.get("tema") else "")
            + "."
        )

    cabeza = (
        f"Titulares sobre {datos['tema']}: "
        if datos.get("tema")
        else "Titulares de hoy: "
    )

    return cabeza + " · ".join(
        re.sub(r"\s+-\s+[^-]+$", "", t["titulo"]) for t in datos["titulares"]
    )


# --- correo urgente ------------------------------------------------------------------------


def correos_urgentes(cuantos: int = 10) -> dict[str, Any]:
    from ai_architect.canales import correo

    if not correo.puede_leer():
        return {"ok": False, "error": "no tengo configurado el correo para leer"}

    leido = correo.leer(cuantos)

    if not leido.get("ok", leido.get("success", False)):
        return {"ok": False, "error": str(leido.get("error", "no pude leer el correo"))}

    mensajes = leido.get("mensajes") or leido.get("correos") or []
    urgentes = [
        m
        for m in mensajes
        if isinstance(m, dict)
        and any(
            p
            in (str(m.get("asunto", "")) + " " + str(m.get("texto", ""))[:300]).lower()
            for p in URGENTE
        )
    ]

    return {"ok": True, "total": len(mensajes), "urgentes": urgentes}


def correos_en_palabras(datos: dict[str, Any]) -> str:
    if not datos.get("ok"):
        return str(datos.get("error"))

    urgentes = datos.get("urgentes") or []

    if not urgentes:
        return (
            f"Leí {datos.get('total', 0)} correo(s) recientes y ninguno parece urgente."
        )

    return f"Tienes {len(urgentes)} correo(s) que parecen urgentes: " + "; ".join(
        f"{m.get('de', '?')}: {m.get('asunto', '')}" for m in urgentes[:3]
    )


# --- por voz ---------------------------------------------------------------------------------


def por_voz(frase: str) -> dict[str, Any] | None:
    limpia = sin_adornos(frase)

    if not limpia:
        return None

    if contiene(limpia, *CLIMA):
        datos = clima(_ciudad_en(limpia))
        salida: dict[str, Any] = {"respuesta": clima_en_palabras(datos)}

        if datos.get("ok"):
            salida["panel"] = {
                "tipo": "texto",
                "titulo": f"Clima en {datos['ciudad']}",
                "cuerpo": json.dumps(datos, ensure_ascii=False, indent=1),
            }

        return salida

    if contiene(limpia, *TRAFICO):
        return {
            "respuesta": (
                "El tráfico en vivo necesita una clave de Google Maps que no tengo. "
                "Si me la das con «configura el tráfico», lo consulto."
            )
        }

    if contiene(limpia, *CORREOS):
        datos = correos_urgentes()

        return {"respuesta": correos_en_palabras(datos)}

    m = NOTICIAS_PIDE.match(limpia)

    if m:
        datos = noticias(m.group("tema") or "")
        salida = {"respuesta": noticias_en_palabras(datos)}

        if datos.get("ok") and datos.get("titulares"):
            salida["panel"] = {
                "tipo": "texto",
                "titulo": "Noticias"
                + (f": {datos['tema']}" if datos.get("tema") else ""),
                "cuerpo": "\n".join(
                    f"• {t['titulo']}"
                    + (f" ({t['fuente']})" if t.get("fuente") else "")
                    for t in datos["titulares"]
                ),
            }

        return salida

    return None


# --- proactivo -------------------------------------------------------------------------------


def alerta_de_lluvia() -> str:
    """Un aviso si va a llover pronto donde estás; vacío si no o si no se sabe."""
    datos = clima()

    if not datos.get("ok"):
        return ""

    prob = datos.get("probabilidad_lluvia_3h")

    if datos.get("lluvia_ahora"):
        return f"Está lloviendo en {datos['ciudad']}."

    if prob is not None and prob >= 70:
        return f"Ojo: hay un {prob} % de lluvia en {datos['ciudad']} en las próximas horas."

    return ""


def aviso_de_correo() -> str:
    datos = correos_urgentes()

    if not datos.get("ok") or not datos.get("urgentes"):
        return ""

    return "Te llegó correo que parece urgente: " + "; ".join(
        f"{m.get('de', '?')}: {m.get('asunto', '')}" for m in datos["urgentes"][:2]
    )
