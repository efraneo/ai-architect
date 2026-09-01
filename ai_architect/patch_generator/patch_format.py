"""
=========================================================
Patch Format

Entender el contenedor de parches, sin tocar el disco.
=========================================================

`PatchLoader` mezclaba dos trabajos: abrir un archivo y entender su formato.
El segundo eran 300 líneas —cabecera, tabla de archivos, extracción del
diff— y con ellas el módulo llegaba a complejidad 24.

Aquí son funciones puras, así que el formato se puede probar dándole texto,
sin escribir un archivo primero. `PatchLoader` se queda con lo suyo: leer
del disco y devolver un `Patch`.

El formato es::

    ID: abc123
    TITLE: ...
    CREATED: 2026-09-01T10:00:00
    APPROVED: true

    FILES
    -----
    MODIFY ruta/al/archivo.py 7 3

    diff --git a/... b/...
"""

from __future__ import annotations

import re

from .models import PatchFile

# Las etiquetas de la cabecera y a qué campo van. Era una cadena de cinco
# ``if line.startswith("X:")`` casi idénticos. Añadir un campo es una línea.
ETIQUETAS: dict[str, str] = {
    "ID:": "id",
    "TITLE:": "title",
    "DESCRIPTION:": "description",
    "CREATED:": "created",
    "APPROVED:": "approved",
}

# Donde acaba la cabecera y empieza el parche de verdad.
INICIO_DEL_DIFF = "diff --git "

# Lo que cuenta como "sí" en la metadata de aprobación.
AFIRMATIVOS = {"true", "1", "yes", "approved"}


def leer_cabecera(text: str) -> tuple[dict[str, str], list[PatchFile]]:
    """Los metadatos y la tabla de archivos, hasta donde empieza el diff.

    La cabecera termina en la primera línea ``diff --git``: de ahí en
    adelante todo es el parche, y ahí no hay nada que interpretar línea a
    línea.
    """
    metadata: dict[str, str] = {}

    files: list[PatchFile] = []

    leyendo_archivos = False

    for line in text.splitlines():
        if line.startswith(INICIO_DEL_DIFF):
            break

        etiqueta = etiqueta_de(line)

        if etiqueta is not None:
            metadata[etiqueta] = valor_de(line)
            continue

        if line.strip() == "FILES":
            leyendo_archivos = True
            continue

        if not leyendo_archivos:
            continue

        desnuda = line.strip()

        # La línea de guiones que separa el encabezado de la tabla.
        if desnuda and set(desnuda) == {"-"}:
            continue

        if not desnuda:
            leyendo_archivos = False
            continue

        entrada = leer_archivo(line)

        if entrada is not None:
            files.append(entrada)

    return metadata, files


def etiqueta_de(line: str) -> str | None:
    """A qué campo corresponde esta línea, si es que a alguno."""
    for prefijo, campo in ETIQUETAS.items():
        if line.startswith(prefijo):
            return campo

    return None


def valor_de(line: str) -> str:
    """Lo que va después del primer ``:``."""
    if ":" not in line:
        return ""

    return line.split(":", 1)[1].strip()


def leer_archivo(line: str) -> PatchFile | None:
    """Una fila de la tabla de archivos.

    El formato actual es ``ACCION ruta añadidas borradas``. Se sigue
    admitiendo el antiguo, ``ACCION ruta``, con los contadores a cero.

    **La ruta puede llevar espacios**, así que los contadores se leen desde
    el final, no por posición. Y si los dos últimos campos no son números,
    todo el resto se toma como ruta: es un parche del formato viejo con un
    nombre raro, no un error.
    """
    partes = line.split()

    if len(partes) < 2:
        return None

    accion = partes[0]

    if len(partes) == 2:
        return PatchFile(path=partes[1], action=accion)

    try:
        añadidas = int(partes[-2])
        borradas = int(partes[-1])

    except ValueError:
        return PatchFile(path=" ".join(partes[1:]), action=accion)

    ruta = " ".join(partes[1:-2])

    if not ruta:
        return None

    return PatchFile(
        path=ruta,
        action=accion,
        additions=añadidas,
        deletions=borradas,
    )


def extraer_diff(text: str) -> str:
    """El diff tal cual, desde ``diff --git`` hasta el final.

    Se corta el texto en crudo a propósito: partir en líneas y volver a
    unirlas destruiría los saltos finales, y un parche que termina en uno o
    en tres no es el mismo para ``git apply``.
    """
    coincidencia = re.search(r"(?m)^diff --git ", text)

    if coincidencia is None:
        return ""

    return text[coincidencia.start() :]


def leer_aprobado(value: str | None) -> bool:
    """La metadata de aprobación, como booleano.

    Sin metadata es ``False``: un parche antiguo no puede volverse
    ejecutable solo por cargarlo.
    """
    if value is None:
        return False

    return value.strip().lower() in AFIRMATIVOS
