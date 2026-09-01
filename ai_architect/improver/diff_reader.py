"""
=========================================================
Diff Reader

Qué archivos toca un parche, y cuánto.
=========================================================

Esto vivía dentro de ``ImprovementEngine``: 100 líneas de parseo de diffs en
medio de un módulo cuyo trabajo es coordinar análisis, plan, pruebas,
decisión, memoria y git. Era la mitad de su complejidad (51) y no tenía nada
que ver con orquestar.

Aquí son funciones puras: se les da texto, devuelven datos. Se pueden probar
sin construir un motor entero.
"""

from __future__ import annotations

import re
from typing import Any

CABECERA = re.compile(r"diff --git a/(.+?) b/(.+)$")

CREAR = "CREATE"

BORRAR = "DELETE"

MODIFICAR = "MODIFY"


def limpiar(diff: str | None) -> str:
    """Quita las vallas de markdown con las que a veces responde el modelo.

    Se le pide un diff a secas, pero un modelo puede envolverlo en ```diff.
    Aplicar un parche con la valla dentro falla siempre.
    """
    if diff is None:
        return ""

    texto = str(diff).strip()

    if not texto.startswith("```"):
        return texto

    lineas = texto.splitlines()

    if lineas:
        lineas = lineas[1:]

    if lineas and lineas[-1].strip() == "```":
        lineas = lineas[:-1]

    return "\n".join(lineas).strip()


# El formato que emiten por defecto los modelos nuevos de OpenAI para editar
# ficheros. Es correcto para su propia herramienta y **no** es un diff
# unificado: `git apply` no lo entiende.
OTRO_FORMATO = "*** Begin Patch"


def formato_ajeno(diff: str) -> str:
    """Si el modelo devolvió un formato de parche que no es un diff, cuál.

    Sin esto, un parche perfectamente intencionado se rechazaba con "Git
    rejected the patch", que hace pensar en un parche corrupto en vez de en
    un malentendido de formato. Con un modelo que emite el suyo por defecto,
    eso es la diferencia entre saber qué arreglar y no saberlo.
    """
    if OTRO_FORMATO in diff:
        return (
            "el modelo devolvió el formato *** Begin Patch de OpenAI "
            "en vez de un diff unificado"
        )

    return ""


def archivos(diff: str) -> list[dict[str, Any]]:
    """Los archivos del parche, con su acción y sus líneas movidas.

    Se admiten las dos formas que llegan: el diff de git completo, con su
    ``diff --git``, y el unificado a secas, que empieza directamente por
    ``---``. Un archivo sin ruta se descarta: no se puede aplicar nada sobre
    algo sin nombre.
    """
    encontrados: list[dict[str, Any]] = []

    actual: dict[str, Any] | None = None

    for linea_cruda in diff.splitlines():
        linea = linea_cruda.rstrip()

        if linea.startswith("diff --git "):
            if actual is not None:
                encontrados.append(actual)

            actual = _nuevo()

            coincidencia = CABECERA.match(linea)

            if coincidencia:
                actual["path"] = coincidencia.group(2)

            continue

        if actual is None:
            if not linea.startswith("--- "):
                continue

            actual = _nuevo()

        _leer(linea, actual)

    if actual is not None:
        encontrados.append(actual)

    return [item for item in encontrados if item["path"]]


def _nuevo() -> dict[str, Any]:
    return {
        "path": "",
        "action": MODIFICAR,
        "additions": 0,
        "deletions": 0,
    }


def _leer(linea: str, actual: dict[str, Any]) -> None:
    """Aplica una línea del diff al archivo que se está leyendo."""
    if linea.startswith("new file mode"):
        actual["action"] = CREAR
        return

    if linea.startswith("deleted file mode"):
        actual["action"] = BORRAR
        return

    if linea.startswith("+++ "):
        _destino(linea[4:].strip(), actual)
        return

    if linea.startswith("--- "):
        # ``--- /dev/null`` significa que el archivo no existía: es un alta.
        if linea[4:].strip() == "/dev/null":
            actual["action"] = CREAR

        return

    if linea.startswith("+"):
        actual["additions"] += 1

    elif linea.startswith("-"):
        actual["deletions"] += 1


def _destino(destino: str, actual: dict[str, Any]) -> None:
    """La línea ``+++``: dice el nombre final, o que el archivo se borra."""
    if destino == "/dev/null":
        actual["action"] = BORRAR

    elif destino.startswith("b/"):
        actual["path"] = destino[2:]

    elif not actual["path"]:
        actual["path"] = destino


# --- Recalcular las cabeceras de los hunks ----------------------------------
#
# Sobre este mismo repositorio, dos llamadas seguidas al mismo modelo con la
# misma instrucción devolvieron el mismo código y dos cabeceras distintas:
#
#     @@ -65,6 +65,11 @@     <- correcta, git la acepta
#     @@ -65,6 +65,12 @@     <- una de más, git la rechaza
#
# El contenido era bueno en las dos. Lo que falla es la aritmética, y esa la
# podemos hacer nosotros: contar las líneas de un hunk es exacto, no es una
# opinión. Solo se tocan los números; ni una línea del código cambia.

CABECERA_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def normalizar(diff: str) -> str:
    """Corrige los contadores de cada ``@@`` según lo que hay debajo."""
    if not diff.strip():
        return diff

    lineas = diff.splitlines()

    salida: list[str] = []

    for indice, linea in enumerate(lineas):
        coincidencia = CABECERA_HUNK.match(linea)

        if coincidencia is None:
            salida.append(linea)
            continue

        viejas, nuevas = _contar(lineas, indice + 1)

        inicio_viejo = coincidencia.group(1)
        inicio_nuevo = coincidencia.group(3)
        cola = coincidencia.group(5)

        salida.append(f"@@ -{inicio_viejo},{viejas} +{inicio_nuevo},{nuevas} @@{cola}")

    final = chr(10).join(salida)

    return final + chr(10) if diff.endswith(chr(10)) else final


def _contar(lineas: list[str], desde: int) -> tuple[int, int]:
    """Cuántas líneas del original y del resultado abarca este hunk."""
    viejas = 0
    nuevas = 0

    for linea in lineas[desde:]:
        if linea.startswith("@@") or linea.startswith(("--- ", "+++ ", "diff --git")):
            break

        if linea.startswith("+"):
            nuevas += 1

        elif linea.startswith("-"):
            viejas += 1

        elif linea.startswith("\\"):
            # "\ No newline at end of file": no cuenta como línea.
            continue

        else:
            # Contexto: cuenta en los dos lados. Una línea vacía del todo
            # también es contexto -- el modelo se come el espacio inicial.
            viejas += 1
            nuevas += 1

    return viejas, nuevas
