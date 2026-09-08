"""Dónde viven las carpetas del usuario y cómo se nombra un archivo sin pisar otro.

``crear`` reexporta estos nombres."""

from __future__ import annotations

import os
import re
import webbrowser
from pathlib import Path


# Dónde se puede guardar sin abrir un diálogo. Los nombres son los que se
# dicen hablando, no los del disco.
def escritorio() -> Path:
    """La carpeta del escritorio, esté donde esté.

    En un Windows en español con OneDrive activo, ``~/Desktop`` **no
    existe**: el escritorio está en ``~/OneDrive/Escritorio``. Dar por
    hecho lo primero es guardar el documento en una carpeta recién creada
    que el usuario no va a mirar nunca.
    """
    candidatas = [
        Path.home() / "OneDrive" / "Escritorio",
        Path.home() / "OneDrive" / "Desktop",
        Path.home() / "Escritorio",
        Path.home() / "Desktop",
    ]

    for carpeta in candidatas:
        if carpeta.is_dir():
            return carpeta

    return Path.home()


def documentos() -> Path:
    for carpeta in (
        Path.home() / "Documents",
        Path.home() / "Documentos",
        Path.home() / "OneDrive" / "Documentos",
    ):
        if carpeta.is_dir():
            return carpeta

    return escritorio()


def _abrir(destino: Path) -> None:
    try:
        webbrowser.open(destino.as_uri())

    except (OSError, ValueError):
        pass


def _sin_pisar(destino: Path) -> Path:
    """Nunca sobrescribe. Un documento perdido no se recupera."""
    if not destino.exists():
        return destino

    for numero in range(2, 100):
        intento = destino.with_name(f"{destino.stem} ({numero}){destino.suffix}")

        if not intento.exists():
            return intento

    return destino.with_name(f"{destino.stem} {os.getpid()}{destino.suffix}")


def _nombre_de_archivo(titulo: str) -> str:
    limpio = re.sub(r"[^\w\s-]", "", titulo, flags=re.UNICODE).strip()

    return (re.sub(r"\s+", " ", limpio) or "documento")[:70]
