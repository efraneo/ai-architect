"""
=========================================================
Historial

El secreto que está commiteado, no el que está en disco.
=========================================================

El agente de seguridad recorre los archivos que hay ahora y encuentra
contraseñas. Eso está bien y no es lo que quema.

Un secreto en el disco se arregla borrándolo. Un secreto **commiteado**
sigue ahí después de borrarlo: está en el historial, lo tiene todo el que
clonó el repositorio, y si el repositorio es público lo tiene cualquiera.
Son dos problemas distintos con dos arreglos distintos, y el agente los
contaba igual.

Esto mira el historial. Es lo que separa "borra esa línea" de "esa clave
está quemada, rótala".

**Lo que cuesta y por qué está acotado.** Recorrer un historial entero es
caro: en un repositorio con años de commits son minutos. Se miran los
últimos ``COMMITS`` y se dice cuántos se miraron. Un resultado parcial que
se presenta como parcial es útil; uno que se presenta como completo, no.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

# Cuántos commits se recorren. Cien cubre lo que se ha tocado hace poco,
# que es donde entran los secretos por descuido.
COMMITS = 100

TIEMPO_LIMITE = 60

# Lo que de verdad quema si está en un commit. Cada patrón busca un
# **valor**, no una palabra: `password` aparece en cualquier proyecto, y
# `password = "hunter2"` es otra cosa.
PATRONES = {
    "clave de OpenAI": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "clave de AWS": re.compile(r"AKIA[0-9A-Z]{16}"),
    "token de GitHub": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "clave de Google": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "clave privada": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "contraseña escrita": re.compile(
        r"""(?i)\b(password|passwd|contrasena|clave)\s*[=:]\s*["'][^"'\s]{6,}["']"""
    ),
    "cadena de conexión": re.compile(
        r"(?i)(mysql|postgres|mongodb)://[^\s:@]+:[^\s@]+@"
    ),
}

# Lo que parece un secreto y no lo es. Sin esto, cada ejemplo de la
# documentación se cuenta como una filtración.
FALSOS = re.compile(
    r"(?i)(tu[_-]?clave|your[_-]?key|xxx+|\.\.\.|ejemplo|example|placeholder|"
    r"sk-proj-xxx|changeme|<[^>]+>)"
)


def hay_git(project: str | Path) -> bool:
    return (Path(project) / ".git").exists()


def revisar(project: str | Path, commits: int = COMMITS) -> dict[str, Any]:
    """Secretos en el historial reciente del repositorio."""
    raiz = Path(project)

    if not hay_git(raiz):
        return {"revisados": 0, "hallazgos": [], "nota": "no es un repositorio git"}

    diferencias = _historial(raiz, commits)

    if diferencias is None:
        return {"revisados": 0, "hallazgos": [], "nota": "no pude leer el historial"}

    hallazgos = _buscar(diferencias)

    return {
        "revisados": commits,
        "hallazgos": hallazgos,
        "nota": (
            f"solo los últimos {commits} commits; un secreto más antiguo "
            "no aparecería aquí"
        ),
    }


def _historial(raiz: Path, commits: int) -> str | None:
    """Los cambios de los últimos commits, en un solo texto."""
    try:
        salida = subprocess.run(
            [
                "git",
                "-C",
                str(raiz),
                "log",
                "-p",
                "--all",
                f"--max-count={commits}",
                # Solo lo que se añadió: lo que se borró ya no está en el
                # árbol, pero sigue en el historial — y es justo lo que se
                # busca, así que se mira el diff entero.
                "--no-color",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=TIEMPO_LIMITE,
        )

    except (OSError, subprocess.SubprocessError):
        return None

    return salida.stdout if salida.returncode == 0 else None


def _buscar(texto: str) -> list[dict[str, Any]]:
    """Los secretos del historial, uno por tipo y sin repetir."""
    hallazgos: list[dict[str, Any]] = []

    commit = ""

    for linea in texto.splitlines():
        if linea.startswith("commit "):
            commit = linea.split()[1][:8]

            continue

        # Solo las líneas añadidas. Una línea borrada en este commit es una
        # que se añadió en otro, y ahí se cuenta.
        if not linea.startswith("+") or linea.startswith("+++"):
            continue

        if FALSOS.search(linea):
            continue

        for que, patron in PATRONES.items():
            if patron.search(linea) is None:
                continue

            if any(h["tipo"] == que and h["commit"] == commit for h in hallazgos):
                continue

            hallazgos.append(
                {
                    "tipo": que,
                    "commit": commit,
                    # **Nunca el valor.** Un informe que reproduce la clave
                    # la filtra otra vez, y encima en un sitio nuevo.
                    "muestra": _tapar(linea.strip()),
                }
            )

    return hallazgos


def _tapar(linea: str) -> str:
    """La línea sin el secreto. Lo suficiente para reconocerla."""
    tapada = linea

    for patron in PATRONES.values():
        tapada = patron.sub("«oculto»", tapada)

    return tapada[:120]


def resumen(revision: dict[str, Any]) -> str:
    """Lo que se dice en voz alta, y qué hacer con ello."""
    hallazgos = revision.get("hallazgos") or []

    if not hallazgos:
        return (
            f"No encontré secretos en los últimos {revision.get('revisados', 0)} "
            "commits."
        )

    tipos = sorted({h["tipo"] for h in hallazgos})

    return (
        f"Hay {len(hallazgos)} secretos en el historial: {', '.join(tipos)}. "
        "Borrarlos del archivo no basta — siguen en los commits y los tiene "
        "quien haya clonado. Hay que rotarlos."
    )
