"""
=========================================================
Env File

Leer un ``.env`` sin depender de nada.
=========================================================

``notifier/`` importaba ``python-dotenv``, que **no está declarado en
``pyproject.toml`` ni instalado**. Es decir: este paquete llevaba tiempo
siendo *inimportable*, y nadie se enteró porque tampoco lo importaba nadie.

Añadir una dependencia entera para leer pares ``CLAVE=valor`` es peor que
no tenerla. Esto son veinte líneas y ningún paquete nuevo.
"""

from __future__ import annotations

import os
from pathlib import Path


def leer(env_file: str | Path) -> dict[str, str]:
    """Devuelve los pares de un archivo ``.env``. Si no existe, ninguno."""
    ruta = Path(env_file)

    if not ruta.is_file():
        return {}

    valores: dict[str, str] = {}

    try:
        lineas = ruta.read_text(encoding="utf-8", errors="ignore").splitlines()

    except OSError:
        return {}

    for linea in lineas:
        limpia = linea.strip()

        if not limpia or limpia.startswith("#") or "=" not in limpia:
            continue

        clave, _, valor = limpia.partition("=")

        clave = clave.strip()

        if clave.startswith("export "):
            clave = clave[len("export ") :].strip()

        valor = valor.strip()

        # Las comillas son del formato del archivo, no parte del valor.
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]

        if clave:
            valores[clave] = valor

    return valores


def valor(
    clave: str,
    env_file: str | Path,
) -> str | None:
    """El valor de ``clave``: primero el entorno, luego el archivo.

    El entorno manda. Un archivo no debe pisar lo que ya se exportó a
    propósito -- que es lo que hacía ``load_dotenv`` sin ``override=False``.
    """
    del_entorno = os.getenv(clave)

    if del_entorno:
        return del_entorno

    return leer(env_file).get(clave)
