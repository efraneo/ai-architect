"""
=========================================================
Git Apply

Aplicar un parche con git, y contar qué pasó.
=========================================================

Eran 130 líneas dentro de `ExecutionPipeline`, un módulo cuyo trabajo es
coordinar validación, aplicación, verificación y rollback. Hacían cuatro
cosas distintas —comprobar el destino, comprobar que es un repositorio,
escribir el parche a un temporal y ejecutar `git apply`— y suponían la mayor
parte de su complejidad (23).

Aquí es una función con un contrato claro: se le da un repositorio y un
diff, y devuelve qué dijo git. Se puede probar sin construir un pipeline.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

TIEMPO_LIMITE = 120

# git no está instalado. 127 es lo que devuelve un shell cuando no encuentra
# el ejecutable, y aquí se respeta para que quien lea el código lo reconozca.
SIN_GIT = 127


def error(
    message: str,
    *,
    stderr: str = "",
    returncode: int = 1,
) -> dict[str, Any]:
    """Un fallo, con la misma forma que un resultado de git."""
    return {
        "success": False,
        "message": message,
        "stdout": "",
        "stderr": stderr,
        "returncode": returncode,
    }


def aplicar(
    repository: Path,
    diff: str,
    *,
    check_only: bool = False,
    reverse: bool = False,
) -> dict[str, Any]:
    """Aplica ``diff`` sobre ``repository``.

    Con ``check_only`` git solo comprueba si el parche encajaría, sin tocar
    nada. Con ``reverse`` lo deshace.

    Nunca lanza: cualquier fallo —destino inexistente, git sin instalar, un
    parche que git rechaza— vuelve como un resultado con ``success: False``,
    porque quien llama tiene que poder decidir con eso en la mano.
    """
    problema = _revisar_destino(repository, diff)

    if problema is not None:
        return problema

    # Que el parche no escriba fuera. `git apply` interpreta las rutas
    # relativas al repositorio y un `../../` en la cabecera sube por el
    # arbol tan tranquilo. Autorizar cambios en un repositorio no es
    # autorizar cambios en el disco, y hasta ahora eran el mismo permiso.
    from ai_architect.core import alcance

    fuera = alcance.revisar(diff, repository)

    if fuera:
        return error(alcance.motivo(fuera, repository))

    temporal: Path | None = None

    try:
        temporal = _escribir(diff)

        resultado = subprocess.run(
            _comando(repository, temporal, check_only, reverse),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=TIEMPO_LIMITE,
        )

        return _informe(resultado, check_only)

    except FileNotFoundError:
        return error(
            "Git executable was not found. "
            "Install Git and ensure it is available on PATH.",
            returncode=SIN_GIT,
        )

    except subprocess.TimeoutExpired:
        return error(
            f"Git did not finish within {TIEMPO_LIMITE} seconds.",
        )

    except OSError as exc:
        return error(f"Git execution error: {exc}", stderr=str(exc))

    finally:
        if temporal is not None:
            try:
                temporal.unlink(missing_ok=True)
            except OSError:
                # No poder borrar un temporal no cambia el resultado, y
                # lanzar desde un `finally` taparía el error de verdad.
                pass


def _revisar_destino(repository: Path, diff: str) -> dict[str, Any] | None:
    """Lo que hay que comprobar antes de molestar a git. ``None`` si todo va."""
    if not repository.exists():
        return error(f"Repository does not exist: {repository}")

    if not repository.is_dir():
        return error(f"Repository is not a directory: {repository}")

    if not diff.strip():
        return error("Patch contains no unified diff.")

    # Esta comprobación estaba **fuera** del `try` del que la llamaba, así
    # que en una máquina sin git reventaba con `FileNotFoundError` antes de
    # llegar al manejador que existe justo para ese caso.
    try:
        comprobacion = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=TIEMPO_LIMITE,
        )

    except FileNotFoundError:
        return error(
            "Git executable was not found. "
            "Install Git and ensure it is available on PATH.",
            returncode=SIN_GIT,
        )

    except subprocess.TimeoutExpired:
        return error(f"Git did not finish within {TIEMPO_LIMITE} seconds.")

    except (OSError, subprocess.SubprocessError) as exc:
        return error(f"Git execution error: {exc}", stderr=str(exc))

    if comprobacion.returncode != 0:
        return {
            "success": False,
            "message": "Target directory is not a Git repository.",
            "stdout": comprobacion.stdout,
            "stderr": comprobacion.stderr,
            "returncode": comprobacion.returncode,
        }

    return None


def _escribir(diff: str) -> Path:
    """El parche en un archivo temporal, con su salto final.

    ``git apply`` rechaza un parche que no termina en salto de línea, y un
    modelo devuelve el diff sin él la mitad de las veces.
    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".patch",
        delete=False,
    ) as manejador:
        manejador.write(diff)

        if not diff.endswith("\n"):
            manejador.write("\n")

        return Path(manejador.name)


def _comando(
    repository: Path,
    parche: Path,
    check_only: bool,
    reverse: bool,
) -> list[str]:
    orden = ["git", "-C", str(repository), "apply"]

    if check_only:
        orden.append("--check")

    if reverse:
        orden.append("--reverse")

    orden.append(str(parche))

    return orden


def _informe(
    resultado: subprocess.CompletedProcess[str],
    check_only: bool,
) -> dict[str, Any]:
    exito = resultado.returncode == 0

    if not exito:
        mensaje = "Git rejected the patch."

    elif check_only:
        mensaje = "Patch validation succeeded."

    else:
        mensaje = "Patch applied successfully."

    return {
        "success": exito,
        "message": mensaje,
        "stdout": resultado.stdout,
        "stderr": resultado.stderr,
        "returncode": resultado.returncode,
    }
