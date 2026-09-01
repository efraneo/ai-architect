"""
=========================================================
Perfil

A quién le habla, y cómo.
=========================================================

Una herramienta que te trata igual el primer día que el año siguiente no se
siente tuya. Esto guarda lo mínimo para que no lo sea: cómo te llamas, cómo
quieres que te llame, y quién la hizo.

Vive en la carpeta del usuario, no en el repositorio: el perfil es de la
persona, no del proyecto que esté analizando en ese momento. Y no lleva ni
una credencial — solo un nombre y un trato.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

CARPETA = Path.home() / ".ai_architect"

ARCHIVO = CARPETA / "perfil.json"

CREADOR_POR_DEFECTO = "Eathan Jiménez — Xentris Tech"

# Los tramos del día. La noche empieza a las 20:00 y llega hasta las 6:00,
# que es cuando alguien que trabaja de madrugada sigue estando de noche.
MANANA = range(6, 12)

TARDE = range(12, 20)


def saludo(ahora: datetime | None = None) -> str:
    """ "Buenos días", "Buenas tardes" o "Buenas noches", según la hora."""
    hora = (ahora or datetime.now()).hour

    if hora in MANANA:
        return "Buenos días"

    if hora in TARDE:
        return "Buenas tardes"

    return "Buenas noches"


def cargar(archivo: Path | None = None) -> dict[str, Any]:
    """El perfil guardado. Si no hay ninguno, uno vacío."""
    destino = archivo or ARCHIVO

    if not destino.is_file():
        return {}

    try:
        datos = json.loads(destino.read_text(encoding="utf-8"))

    except (OSError, ValueError):
        # Un perfil ilegible no puede impedir trabajar: se ignora y se sigue.
        return {}

    return dict(datos) if isinstance(datos, dict) else {}


def guardar(
    datos: dict[str, Any],
    archivo: Path | None = None,
) -> bool:
    """Guarda el perfil. Devuelve si se pudo."""
    destino = archivo or ARCHIVO

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)

        destino.write_text(
            json.dumps(datos, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    except OSError:
        return False

    return True


def esta_configurado(archivo: Path | None = None) -> bool:
    return bool(cargar(archivo).get("tratamiento"))


def configurar(
    tratamiento: str,
    nombre: str = "",
    creador: str = CREADOR_POR_DEFECTO,
    archivo: Path | None = None,
) -> dict[str, Any]:
    """Deja constancia de cómo hay que dirigirse a esta persona."""
    datos = {
        "nombre": nombre.strip() or tratamiento.strip(),
        "tratamiento": tratamiento.strip(),
        "creador": creador.strip(),
        "configurado": datetime.now().isoformat(timespec="seconds"),
    }

    guardar(datos, archivo)

    return datos


def como_llamarte(archivo: Path | None = None) -> str:
    """El trato preferido. Sin perfil, el nombre de usuario del sistema."""
    tratamiento = cargar(archivo).get("tratamiento")

    if tratamiento:
        return str(tratamiento)

    return os.getenv("USERNAME") or os.getenv("USER") or "jefe"


def encabezar(archivo: Path | None = None, ahora: datetime | None = None) -> str:
    """Cómo empieza una respuesta: saludo y trato.

    Ejemplo: ``Buenas noches, Eathan.``
    """
    return f"{saludo(ahora)}, {como_llamarte(archivo)}."


def despedir(archivo: Path | None = None, ahora: datetime | None = None) -> str:
    """Cómo termina. El mismo tramo del día, para cerrar el círculo."""
    momento = {
        "Buenos días": "Que tengas buen día",
        "Buenas tardes": "Buena tarde",
        "Buenas noches": "Buena noche",
    }[saludo(ahora)]

    return f"{momento}, {como_llamarte(archivo)}."


def quien_te_hizo(archivo: Path | None = None) -> str:
    return str(cargar(archivo).get("creador") or CREADOR_POR_DEFECTO)
