"""
=========================================================
ChangeLog Builder

De los commits de git a una entrada de changelog.
=========================================================

`changelog/` sabía guardar y escribir entradas, pero nadie las construía:
faltaba la pieza que mira el repositorio y dice qué ha cambiado. Es lo que
lo mantenía huérfano.

Se apoya en dos cosas que ya están conectadas: ``TagManager.latest()`` para
saber desde dónde contar, y ``CommitManager.history()`` para leer los
commits con sus estadísticas por archivo.
"""

from __future__ import annotations

import re
from pathlib import Path

from ai_architect.git.commit_manager import CommitManager
from ai_architect.git.tag_manager import TagManager

from .models import ChangeItem, ChangeLogEntry, ChangeType

# Prefijos de commit convencional -> tipo de cambio. Se mira el asunto del
# commit, que es lo único que describe la intención; los números de líneas
# dicen cuánto cambió, no por qué.
PREFIJOS: tuple[tuple[str, ChangeType], ...] = (
    ("fix", ChangeType.FIX),
    ("bugfix", ChangeType.FIX),
    ("hotfix", ChangeType.FIX),
    ("refactor", ChangeType.REFACTOR),
    ("perf", ChangeType.REFACTOR),
    ("feat", ChangeType.CREATE),
    ("add", ChangeType.CREATE),
    ("remove", ChangeType.DELETE),
    ("delete", ChangeType.DELETE),
    ("revert", ChangeType.DELETE),
)

# "feat(scope): asunto" y "fix!: asunto" también cuentan.
CONVENCIONAL = re.compile(r"^([a-záéíóúñ]+)(\([^)]*\))?!?:", re.IGNORECASE)


class ChangeLogBuilder:
    def __init__(
        self,
        repository: str | Path,
    ) -> None:
        self.repository = Path(repository).resolve()

        self.commits = CommitManager(str(self.repository))

        self.tags = TagManager(self.repository)

    def desde_la_ultima_etiqueta(self) -> str:
        """Desde dónde contar. Sin etiquetas, desde el principio."""
        return self.tags.latest()

    def build(
        self,
        version: str = "",
        author: str = "AI Architect",
        since: str | None = None,
    ) -> ChangeLogEntry:
        """La entrada de esta versión, a partir de los commits.

        ``since`` por defecto es la última etiqueta: el changelog cubre lo
        que va de la versión anterior a hoy.
        """
        referencia = self.desde_la_ultima_etiqueta() if since is None else since

        entrada = ChangeLogEntry(
            version=version or "sin versión",
            author=author,
        )

        # Un ítem por **commit**, no por archivo. La primera versión hacía lo
        # segundo y sobre este repositorio salían 643 líneas, casi todas
        # repitiendo el mismo asunto: eso no es un changelog, es un `git log`
        # mal formateado. Los archivos se resumen en el propio ítem.
        for commit in self.commits.history(since=referencia):
            asunto = str(commit.get("subject", ""))

            archivos = commit.get("files")
            archivos = archivos if isinstance(archivos, list) else []

            añadidas = 0
            borradas = 0
            rutas: list[str] = []

            for archivo in archivos:
                if not isinstance(archivo, dict):
                    continue

                añadidas += int(archivo.get("additions", 0) or 0)
                borradas += int(archivo.get("deletions", 0) or 0)

                ruta = str(archivo.get("path", "")).strip()

                if ruta:
                    rutas.append(ruta)

            entrada.add(
                ChangeItem(
                    file=resumir(rutas),
                    change_type=clasificar(asunto),
                    summary=asunto,
                    additions=añadidas,
                    deletions=borradas,
                )
            )

        return entrada


def clasificar(asunto: str) -> ChangeType:
    """Qué clase de cambio anuncia el asunto de un commit.

    Se acepta tanto el formato convencional (``fix(agents): ...``) como la
    primera palabra a secas (``Arregla ...`` no casa; ``fix ...`` sí). Lo que
    no se reconoce es ``UPDATE``: la mayoría de los commits son eso, y
    inventarles una categoría sería peor que dejarlos donde están.
    """
    limpio = asunto.strip().lower()

    if not limpio:
        return ChangeType.UPDATE

    coincidencia = CONVENCIONAL.match(limpio)

    palabra = coincidencia.group(1) if coincidencia else limpio.split(" ")[0]

    for prefijo, tipo in PREFIJOS:
        if palabra == prefijo:
            return tipo

    return ChangeType.UPDATE


def resumir(rutas: list[str]) -> str:
    """Los archivos de un commit, en una línea.

    Uno se nombra; varios se cuentan y se dice la carpeta común, que es lo
    que de verdad orienta: "12 archivos en ai_architect/agents" dice mucho
    más que doce rutas seguidas.
    """
    if not rutas:
        return ""

    if len(rutas) == 1:
        return rutas[0]

    carpetas = {ruta.rsplit("/", 1)[0] for ruta in rutas if "/" in ruta}

    if len(carpetas) == 1:
        return f"{len(rutas)} archivos en {carpetas.pop()}"

    return f"{len(rutas)} archivos"
