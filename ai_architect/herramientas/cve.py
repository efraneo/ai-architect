"""
=========================================================
CVE

Fallos conocidos de verdad, no dependencias antiguas.
=========================================================

El agente de dependencias sabía decir "hay librerías desactualizadas". Eso
no es un hallazgo: es una observación que vale para cualquier proyecto de
más de un año, y quien la lee no sabe si tiene que hacer algo hoy o no.

Esto pregunta a **osv.dev**, la base de vulnerabilidades de Google —
gratis, sin clave y sin límite razonable— y devuelve lo que de verdad
tiene un fallo publicado, con su identificador y su gravedad.

**Lo que no puede hacer, y conviene decirlo.** Aquí se leen las versiones
*declaradas*, no las instaladas. Un `openai>=1.40.0` no dice qué versión
hay en la máquina: dice cuál es la más antigua que el proyecto acepta. Se
consulta esa, que es el peor caso que el proyecto permite, y se avisa de
que es una cota y no una foto.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

OSV = "https://api.osv.dev/v1/querybatch"

DETALLE = "https://api.osv.dev/v1/vulns/"

# Sin red no se espera eternamente: el agente tiene que poder contestar
# aunque la consulta no salga.
TIEMPO_LIMITE = 12

# Cuántos fallos se detallan. Los demás se cuentan: una lista de treinta
# identificadores no la lee nadie, y menos escuchándola.
DETALLES = 5

DECLARACIONES = ("requirements.txt", "pyproject.toml")

# `paquete==1.2.3`, `paquete>=1.2.3`, `paquete ~= 1.2` y sus variantes.
LINEA = re.compile(
    r"^\s*[\"']?([A-Za-z0-9][A-Za-z0-9._-]*)[\"']?\s*(?:\[[^\]]*\])?\s*"
    r"(?:==|>=|~=|>)\s*[\"']?(\d[\w.\-]*)",
)


def dependencias(project: str | Path) -> list[tuple[str, str]]:
    """Los paquetes declarados y la versión más baja que aceptan."""
    raiz = Path(project)

    encontradas: dict[str, str] = {}

    for nombre in DECLARACIONES:
        archivo = raiz / nombre

        if not archivo.is_file():
            continue

        try:
            texto = archivo.read_text(encoding="utf-8", errors="ignore")

        except OSError:
            continue

        for linea in texto.splitlines():
            if linea.strip().startswith("#"):
                continue

            hallado = LINEA.match(linea)

            if hallado is not None:
                encontradas.setdefault(hallado.group(1).lower(), hallado.group(2))

    return sorted(encontradas.items())


def revisar(project: str | Path) -> dict[str, Any]:
    """Los fallos conocidos de lo que declara el proyecto."""
    paquetes = dependencias(project)

    if not paquetes:
        return {"consultado": 0, "vulnerables": [], "nota": "no encontré dependencias"}

    respuesta = _preguntar(paquetes)

    if respuesta is None:
        return {
            "consultado": 0,
            "vulnerables": [],
            "nota": "no pude consultar osv.dev; puede que no haya internet",
        }

    vulnerables = []

    for (nombre, version), hallazgo in zip(paquetes, respuesta, strict=False):
        ids = [v.get("id") for v in (hallazgo or {}).get("vulns") or []]

        if ids:
            vulnerables.append({"paquete": nombre, "version": version, "fallos": ids})

    return {
        "consultado": len(paquetes),
        "vulnerables": vulnerables,
        "detalle": _detallar(vulnerables),
        "nota": (
            "versiones declaradas, no instaladas: es la más antigua que el "
            "proyecto acepta, o sea el peor caso que permite"
        ),
    }


def _preguntar(paquetes: list[tuple[str, str]]) -> list[dict[str, Any]] | None:
    cuerpo = json.dumps(
        {
            "queries": [
                {"package": {"name": nombre, "ecosystem": "PyPI"}, "version": version}
                for nombre, version in paquetes
            ]
        }
    ).encode("utf-8")

    peticion = urllib.request.Request(
        OSV, data=cuerpo, headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(peticion, timeout=TIEMPO_LIMITE) as red:
            datos = json.loads(red.read().decode("utf-8"))

    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        # Sin red se dice que no se pudo. Contestar "ninguna vulnerabilidad"
        # porque no se llegó a preguntar sería la peor forma de fallar.
        return None

    resultados = datos.get("results")

    return resultados if isinstance(resultados, list) else None


def _detallar(vulnerables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Qué es cada fallo, para los primeros. Los demás se cuentan."""
    detalles: list[dict[str, Any]] = []

    for entrada in vulnerables:
        for identificador in entrada["fallos"][:2]:
            if len(detalles) >= DETALLES:
                return detalles

            ficha = _ficha(str(identificador))

            if ficha:
                detalles.append({**ficha, "paquete": entrada["paquete"]})

    return detalles


def _ficha(identificador: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(
            DETALLE + identificador, timeout=TIEMPO_LIMITE
        ) as red:
            datos = json.loads(red.read().decode("utf-8"))

    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return {}

    return {
        "id": identificador,
        "resumen": str(datos.get("summary") or "")[:220],
        "gravedad": _gravedad(datos),
    }


def _gravedad(datos: dict[str, Any]) -> str:
    """La gravedad dicha en una palabra, no en un vector CVSS.

    "CVSS:3.1/AV:N/AC:L/PR:N" es exacto y no lo entiende nadie de oído.
    """
    for entrada in datos.get("severity") or []:
        puntuacion = str(entrada.get("score") or "")

        for nivel, palabra in (
            ("/C:H", "alta"),
            ("/C:L", "media"),
        ):
            if nivel in puntuacion:
                return palabra

    return "sin clasificar"
