"""Buscar en el código sin depender de rg ni de grep.

En la prueba real el modelo quiso buscar con ``rg``, que en esta máquina no
está, y el cambio se quedó en la cola de permisos para fallar al aprobarse.
Esta herramienta busca en Python, dentro del repositorio, y no cambia nada:
no pide permiso y no necesita nada instalado.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ai_architect.agente.herramientas_base import BaseTool, ToolSpec
from ai_architect.agente.tipos import ToolResult

MAX_RESULTADOS = 200
MAX_ARCHIVOS = 6000

CARPETAS_AJENAS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "dist",
    "dist_tmp",
    "build",
    "build_tmp",
    "salida",
}

TEXTO = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".cmd",
    ".bat",
    ".ps1",
    ".sh",
    ".ini",
    ".cfg",
    ".iss",
    ".spec",
    ".env",
    ".sql",
    ".xml",
    ".csv",
}


def buscar(
    raiz: Path,
    patron: str,
    ruta: str = "",
    extension: str = "",
    contexto: int = 0,
    maximo: int = MAX_RESULTADOS,
) -> list[str]:
    """Líneas «archivo:línea: texto» que casan con el patrón (regex, sin mayúsculas)."""
    try:
        expresion = re.compile(patron, re.IGNORECASE)

    except re.error:
        expresion = re.compile(re.escape(patron), re.IGNORECASE)

    base = (raiz / ruta).resolve() if ruta else raiz.resolve()

    if not str(base).startswith(str(raiz.resolve())):
        return []

    extensiones = {
        "." + e.strip().lstrip(".").lower() for e in extension.split(",") if e.strip()
    } or TEXTO
    salida: list[str] = []
    vistos = 0
    archivos = [base] if base.is_file() else sorted(base.rglob("*"))

    for archivo in archivos:
        if not archivo.is_file() or archivo.suffix.lower() not in extensiones:
            continue

        if any(p in CARPETAS_AJENAS for p in archivo.relative_to(raiz.resolve()).parts):
            continue

        vistos += 1

        if vistos > MAX_ARCHIVOS:
            break

        try:
            lineas = archivo.read_text(encoding="utf-8", errors="ignore").splitlines()

        except OSError:
            continue

        relativo = archivo.relative_to(raiz.resolve()).as_posix()

        for numero, texto in enumerate(lineas, 1):
            if not expresion.search(texto):
                continue

            if contexto:
                desde, hasta = max(0, numero - 1 - contexto), min(
                    len(lineas), numero + contexto
                )

                for k in range(desde, hasta):
                    marca = ":" if k == numero - 1 else "-"
                    salida.append(
                        f"{relativo}:{k + 1}{marca} {lineas[k].rstrip()[:200]}"
                    )

                salida.append("--")

            else:
                salida.append(f"{relativo}:{numero}: {texto.strip()[:200]}")

            if len(salida) >= maximo:
                return salida

    return salida


class BuscarEnCodigoTool(BaseTool):
    tool_id = "buscar_en_codigo"

    def __init__(self, raiz: str) -> None:
        self._raiz = Path(raiz)

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="buscar_en_codigo",
            description=(
                "Busca un patrón (expresión regular, sin distinguir mayúsculas) en los archivos del "
                "repositorio y devuelve archivo:línea: texto. Úsala en vez de rg o grep: no depende "
                "de nada instalado y no pide permiso. ruta acota a una carpeta o archivo; extension "
                "filtra («py», «py,html»); contexto añade líneas alrededor."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "patron": {"type": "string"},
                    "ruta": {"type": "string"},
                    "extension": {"type": "string"},
                    "contexto": {"type": "integer"},
                },
                "required": ["patron"],
            },
            category="filesystem",
        )

    def execute(self, **params: Any) -> ToolResult:
        patron = str(params.get("patron", "")).strip()

        if not patron:
            return ToolResult(
                tool_name=self.tool_id, content="Falta el patrón.", success=False
            )

        try:
            contexto = int(params.get("contexto") or 0)

        except (TypeError, ValueError):
            contexto = 0

        lineas = buscar(
            self._raiz,
            patron,
            str(params.get("ruta", "") or ""),
            str(params.get("extension", "") or ""),
            max(0, min(contexto, 6)),
        )

        if not lineas:
            return ToolResult(
                tool_name=self.tool_id,
                content=f"Nada casa con «{patron}».",
                success=True,
            )

        cabeza = f"{len(lineas)} línea(s)" + (
            " (recortado)" if len(lineas) >= MAX_RESULTADOS else ""
        )

        return ToolResult(
            tool_name=self.tool_id,
            content=cabeza + ":\n" + "\n".join(lineas),
            success=True,
        )
