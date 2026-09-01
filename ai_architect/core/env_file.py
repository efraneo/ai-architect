"""
=========================================================
Env File

Leer un ``.env`` sin depender de nada.
=========================================================

``notifier/`` importaba ``python-dotenv``, que **no está declarado en
``pyproject.toml`` ni instalado**. Es decir: aquel paquete llevaba tiempo
siendo *inimportable*, y nadie se enteró porque tampoco lo importaba nadie.

Añadir una dependencia entera para leer pares ``CLAVE=valor`` es peor que
no tenerla. Esto son treinta líneas y ningún paquete nuevo.

Vive en ``core/`` porque no es cosa del notificador: **el arquitecto entero
no leía ningún ``.env``**. Se podía poner la clave del proveedor en el
archivo que el propio ``.env.example`` sugiere y ``doctor`` seguía diciendo
``not_configured``, porque los proveedores solo miraban ``os.getenv``. Había
que exportarla a mano en cada sesión.
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


def cargar(env_file: str | Path = ".env") -> list[str]:
    """Mete en el entorno lo que declare el archivo, **sin pisar nada**.

    Lo que ya esté exportado manda: quien escribe
    ``OPENAI_API_KEY=... architect improve`` está diciendo a propósito que
    quiere esa y no la del archivo.

    Devuelve los nombres de lo que cargó, para poder decirlo si hace falta.
    Nunca los valores.
    """
    cargadas: list[str] = []

    for clave, valor in leer(env_file).items():
        if os.getenv(clave):
            continue

        os.environ[clave] = valor

        cargadas.append(clave)

    return cargadas


def raiz_del_paquete() -> Path:
    """La carpeta del proyecto instalado, subiendo desde este archivo.

    Con ``pip install -e .`` es el propio repositorio, que es donde vive el
    ``.env`` de verdad.
    """
    return Path(__file__).resolve().parent.parent.parent


def cargar_todo(project: str | Path | None = None) -> list[str]:
    """El ``.env`` de la sesión, el del proyecto analizado y el del paquete.

    Buscarlo solo en el directorio actual hace que la clave dependa de
    **desde dónde** se llame. Lanzando el arquitecto con un acceso directo,
    o con un ``.cmd`` desde otra carpeta, el ``.env`` del repositorio queda
    fuera de alcance y el proveedor contesta ``not_configured`` teniendo la
    clave escrita a dos carpetas de distancia.

    El orden es el de la prioridad, y ninguno pisa al anterior: lo que ya
    está exportado manda sobre los tres.
    """
    sitios: list[Path] = [Path.cwd()]

    if project:
        sitios.append(Path(project))

    sitios.append(raiz_del_paquete())

    cargadas: list[str] = []
    vistos: set[Path] = set()

    for sitio in sitios:
        try:
            carpeta = sitio.resolve()

        except OSError:
            continue

        if carpeta in vistos:
            continue

        vistos.add(carpeta)

        cargadas.extend(cargar(carpeta / ".env"))

    return cargadas
