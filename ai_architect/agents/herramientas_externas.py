"""Lo que los agentes ejecutan de verdad: ruff, mypy, black, git, gh, pip.

Cada agente estático hacía expresiones regulares sobre el árbol. Con esto
corren las herramientas que un ingeniero correría, dentro del intérprete del
proyecto si tiene uno, con tope de tiempo y sin reventar si falta alguna.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

TIEMPO = 120


def python_de(raiz: Path) -> str:
    """El intérprete del proyecto (su .venv) o el propio."""
    venv = (
        raiz
        / ".venv"
        / ("Scripts" if os.name == "nt" else "bin")
        / ("python.exe" if os.name == "nt" else "python")
    )

    return str(venv) if venv.is_file() else sys.executable


def hay(programa: str) -> bool:
    return shutil.which(programa) is not None


def modulo_disponible(raiz: Path, modulo: str) -> bool:
    """Si ``python -m <modulo>`` existe en el intérprete del proyecto."""
    try:
        salida = subprocess.run(
            [python_de(raiz), "-c", f"import {modulo}"],
            capture_output=True,
            timeout=30,
        )

    except (OSError, subprocess.SubprocessError):
        return False

    return salida.returncode == 0


def correr(
    orden: list[str], cwd: Path, timeout: float = TIEMPO
) -> tuple[int, str, str]:
    """``(código, stdout, stderr)``. Un fallo al lanzar cuenta como código -1."""
    try:
        salida = subprocess.run(
            orden,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

    except (OSError, subprocess.SubprocessError) as e:
        return -1, "", str(e)

    return salida.returncode, salida.stdout or "", salida.stderr or ""


def correr_json(orden: list[str], cwd: Path, timeout: float = TIEMPO) -> Any:
    """Lo mismo, con la salida parseada como JSON (o ``None``)."""
    _, out, _ = correr(orden, cwd, timeout)

    try:
        return json.loads(out) if out.strip() else None

    except ValueError:
        return None


def relativo(ruta: str, raiz: Path) -> str:
    try:
        return str(Path(ruta).resolve().relative_to(raiz.resolve()))

    except (ValueError, OSError):
        return ruta
