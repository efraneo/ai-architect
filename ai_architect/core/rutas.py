"""
=========================================================
Rutas

De un nombre dicho en voz alta a una carpeta de verdad.
=========================================================

Hablando no se dictan rutas. Nadie dice "ce dos puntos barra software guion
bajo phyton barra AI guion architect": se dice *"revisa autosgsst"*, y hay
que saber de qué carpeta habla.

Esto busca esa carpeta donde tiene sentido que esté —dentro del proyecto
actual, junto a él, en la carpeta del usuario y en las raíces donde de
hecho vive el código de esta máquina— y devuelve la que más se parece.

Dos decisiones que importan:

- **No se baja por todo el disco.** Un recorrido completo tarda minutos y
  encuentra cientos de `src`. Se miran dos niveles desde unas pocas raíces.
- **Si no está claro, no se elige.** Ejecutar algo sobre la carpeta
  equivocada es peor que preguntar, así que ante la duda se devuelven las
  candidatas para poder decirlas en voz alta.
"""

from __future__ import annotations

import os
from difflib import SequenceMatcher
from pathlib import Path

from ai_architect.core.texto import sin_adornos

# Lo que nunca es lo que se busca, y lo que llenaría la lista de ruido.
IGNORADAS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "site-packages",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

# Hasta dónde se baja desde cada raíz. Dos niveles cubren
# `C:\código\proyecto` y `C:\código\proyecto\módulo`, que es donde está todo.
HONDURA = 2

# Por encima de esto se da por buena. Por debajo, se pregunta.
PARECIDO = 0.72


def raices(base: Path) -> list[Path]:
    """Dónde tiene sentido buscar, en orden de cercanía.

    Primero el proyecto en el que se está: si se dice un nombre mientras se
    trabaja en un repositorio, casi siempre es algo de dentro.
    """
    candidatas = [base, base.parent, Path.home()]

    # Las raíces donde de hecho vive el código en esta máquina. Se leen del
    # entorno para no dejar una ruta de nadie escrita en el código.
    extra = os.getenv("AI_ARCHITECT_RAICES", "")

    candidatas.extend(Path(p.strip()) for p in extra.split(os.pathsep) if p.strip())

    vistas: list[Path] = []

    for ruta in candidatas:
        try:
            resuelta = ruta.resolve()

        except OSError:
            continue

        if resuelta.is_dir() and resuelta not in vistas:
            vistas.append(resuelta)

    return vistas


def carpetas(base: Path) -> list[Path]:
    """Las carpetas candidatas, sin bajar por todo el disco."""
    encontradas: list[Path] = []
    vistas: set[Path] = set()

    for raiz in raices(base):
        _recoger(raiz, HONDURA, encontradas, vistas)

    return encontradas


def _recoger(
    carpeta: Path,
    hondura: int,
    encontradas: list[Path],
    vistas: set[Path],
) -> None:
    if hondura <= 0:
        return

    try:
        hijas = list(carpeta.iterdir())

    except OSError:
        # Una carpeta sin permisos no puede parar la búsqueda entera.
        return

    for hija in hijas:
        if not hija.is_dir() or hija.name in IGNORADAS or hija.name.startswith("."):
            continue

        if hija in vistas:
            continue

        vistas.add(hija)
        encontradas.append(hija)

        _recoger(hija, hondura - 1, encontradas, vistas)


def resolver(nombre: str, base: Path | str = ".") -> tuple[Path | None, list[Path]]:
    """La carpeta que se quiso decir, y las que se le parecen.

    Devuelve ``(elegida, parecidas)``. Si no hay una clara, ``elegida`` es
    ``None`` y ``parecidas`` trae con qué preguntar.
    """
    buscado = sin_adornos(nombre)

    if not buscado:
        return (None, [])

    raiz = Path(base).resolve()

    # Si lo que dijo ya es una ruta, no hay nada que adivinar.
    directa = Path(nombre.strip().strip("\"'"))

    if directa.is_dir():
        return (directa.resolve(), [])

    puntuadas: list[tuple[float, Path]] = []

    for carpeta in carpetas(raiz):
        limpio = sin_adornos(carpeta.name)

        if limpio == buscado:
            return (carpeta, [])

        if buscado in limpio or limpio in buscado:
            puntuadas.append((0.9, carpeta))

            continue

        parecido = SequenceMatcher(None, buscado, limpio).ratio()

        if parecido >= 0.55:
            puntuadas.append((parecido, carpeta))

    puntuadas.sort(key=lambda par: par[0], reverse=True)

    if not puntuadas:
        return (None, [])

    mejor, cual = puntuadas[0]

    # Una sola buena candidata basta; dos igual de buenas, no. Elegir a
    # ciegas entre dos carpetas que suenan igual es exactamente lo que no
    # hay que hacer con algo que va a ejecutar comandos.
    segunda = puntuadas[1][0] if len(puntuadas) > 1 else 0.0

    if mejor >= PARECIDO and mejor - segunda > 0.05:
        return (cual, [])

    return (None, [c for _, c in puntuadas[:6]])


def nombrar(rutas: list[Path]) -> str:
    """Las carpetas, dichas como se dicen en voz alta."""
    return ", ".join(r.name for r in rutas)
