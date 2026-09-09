"""La caja de herramientas que Architect lleva a un repositorio.

Todas las herramientas quedan acotadas al repositorio: leer y escribir solo dentro de él, la
consola arranca en él, y git actúa sobre él. Las que modifican algo piden confirmación al
``ToolExecutor``; sin permiso, el agente recibe una negativa y propone en vez de tocar.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from typing import Any

from ai_architect.agente.herramientas.buscar import BuscarEnCodigoTool
from ai_architect.agente.herramientas.escribir import FileWriteTool
from ai_architect.agente.herramientas.git import (
    GitCommitTool,
    GitDiffTool,
    GitLogTool,
    GitStatusTool,
)
from ai_architect.agente.herramientas.instalar import InstalarTool
from ai_architect.agente.herramientas.leer import FileReadTool
from ai_architect.agente.herramientas.parche import ApplyPatchTool
from ai_architect.agente.herramientas.shell import ShellExecTool
from ai_architect.agente.herramientas_base import BaseTool, ToolSpec
from ai_architect.agente.tipos import ToolResult

# Nombres de las herramientas que cambian el repositorio o ejecutan cosas.
ESCRIBEN = frozenset(
    {
        "file_write",
        "apply_patch",
        "shell_exec",
        "git_commit",
        # Lo que sale de la máquina o la cambia también pide permiso.
        "enviar_telegram",
        "enviar_correo",
        "enviar_whatsapp",
        "celular_llamar",
        # Las órdenes al equipo que cambian algo (formatear, commit, subir, actualizar…).
        "ordenar",
    }
)


class _ConPermiso:
    """En OpenJarvis `file_write` y `apply_patch` no pedían confirmación (la auditoría lo marcó).
    Aquí TODO lo que escribe pasa por la puerta de confirmación del ejecutor."""

    @property
    def spec(self) -> ToolSpec:  # type: ignore[override]
        base: ToolSpec = super().spec  # type: ignore[misc]
        return dataclasses.replace(base, requires_confirmation=True)


class EscribirConPermiso(_ConPermiso, FileWriteTool):
    pass


class ParcheConPermiso(_ConPermiso, ApplyPatchTool):
    pass


class ShellConPermiso(_ConPermiso, ShellExecTool):
    """La consola pide permiso salvo para lo que solo mira: rg, grep, ls, git status,
    pytest, ruff… Buscar en el código no debería esperar a nadie."""

    def sin_confirmacion(self, params: dict[str, Any]) -> bool:
        return es_solo_lectura(str(params.get("command", "")))

    def execute(self, **params: Any) -> ToolResult:
        resultado = super().execute(**params)

        # «rg no se reconoce…» en la prueba real: se dice claro y se ofrece lo propio.
        if not resultado.success and _programa_ausente(str(resultado.content)):
            orden = str(params.get("command", "")).split()
            programa = orden[0] if orden else "ese programa"
            pista = (
                " Para buscar en el código usa la herramienta buscar_en_codigo."
                if programa in ("rg", "grep", "findstr", "ag", "ack")
                else " Si hace falta, instálalo con la herramienta instalar o dilo."
            )

            return ToolResult(
                tool_name=resultado.tool_name,
                content=f"«{programa}» no está instalado en esta máquina." + pista,
                success=False,
                metadata=resultado.metadata,
            )

        return resultado


def _programa_ausente(salida: str) -> bool:
    texto = salida.lower()

    return (
        "no se reconoce como un comando" in texto
        or "is not recognized as" in texto
        or "command not found" in texto
        or "no such file or directory" in texto
        and "execvp" in texto
    )


SOLO_LECTURA = frozenset(
    {
        "rg",
        "grep",
        "findstr",
        "ls",
        "dir",
        "cat",
        "type",
        "head",
        "tail",
        "wc",
        "find",
        "tree",
        "echo",
        "where",
        "which",
        "pwd",
        "pytest",
        "ruff",
        "mypy",
        "black",
        "bandit",
        "pip-audit",
        "npm",
        "node",
        "git",
        "python",
        "python3",
        "py",
    }
)

GIT_LECTURA = frozenset(
    {
        "status",
        "diff",
        "log",
        "show",
        "ls-files",
        "branch",
        "blame",
        "grep",
        "rev-parse",
        "describe",
        "tag",
        "remote",
    }
)
PYTHON_LECTURA = (
    "-m pytest",
    "-m ruff",
    "-m mypy",
    "-m black --check",
    "-m bandit",
    "-m pip_audit",
    "-m pip list",
    "-m pip show",
    "-c ",
)
NPM_LECTURA = (
    "audit",
    "ls",
    "list",
    "outdated",
    "view",
    "test",
    "run test",
    "run lint",
)
PELIGRO = re.compile(
    r"(>>?|\|\s*(?:tee|sh|bash|cmd|powershell)\b|\brm\b|\bdel\b|\bmv\b|\bcp\b|\bmkdir\b|\brmdir\b|\bcurl\b|\bwget\b|\bInvoke-|\bSet-|\bRemove-|\bpip install\b|--fix\b|\bnpm (?:install|i|ci|uninstall|publish)\b)"
)


def es_solo_lectura(orden: str) -> bool:
    """Si una orden de consola solo mira. Ante la duda, no."""
    limpia = orden.strip()

    if not limpia or "&&" in limpia or ";" in limpia or "`" in limpia or "$(" in limpia:
        return False

    if PELIGRO.search(limpia):
        return False

    partes = limpia.split()
    programa = partes[0].lower().rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    programa = programa[:-4] if programa.endswith(".exe") else programa

    if programa not in SOLO_LECTURA:
        return False

    if programa == "git":
        return len(partes) > 1 and partes[1] in GIT_LECTURA

    if programa in ("python", "python3", "py"):
        resto = " ".join(partes[1:])

        return resto.startswith(PYTHON_LECTURA) and " -m pip install" not in resto

    if programa == "npm":
        return (
            len(partes) > 1
            and " ".join(partes[1:3]) in NPM_LECTURA
            or (len(partes) > 1 and partes[1] in NPM_LECTURA)
        )

    if programa == "node":
        return len(partes) > 1 and partes[1] in ("--version", "-v")

    if programa == "black":
        return "--check" in partes or "--diff" in partes

    return True


class CommitConPermiso(_ConPermiso, GitCommitTool):
    pass


# Los clientes MCP vivos: si se recogen como basura se cierran las conexiones.
_clientes_mcp: list[Any] = []


def herramientas_para(
    repositorio: Path,
    *,
    con_skills: bool = False,
    con_mcp: bool = False,
    confirmar: Any = None,
    bus: Any = None,
) -> list[BaseTool]:
    """La caja base y, si se pide, las skills en carpeta y las herramientas MCP.

    Las skills corren sus pasos con un ejecutor sobre la caja base, con la misma política
    de permisos (``confirmar``). Un fallo al descubrir skills o servidores MCP no puede
    dejar al agente sin su caja: se ignora y se sigue con lo básico.
    """
    raiz = str(Path(repositorio).resolve())
    base: list[BaseTool] = [
        FileReadTool(allowed_dirs=[raiz]),
        EscribirConPermiso(allowed_dirs=[raiz]),
        ParcheConPermiso(),
        ShellConPermiso(),
        GitStatusTool(),
        GitDiffTool(),
        GitLogTool(),
        CommitConPermiso(),
        # Procurarse lo que falte (paquetes, skills) pide permiso.
        InstalarTool(requisitos=str(Path(raiz) / "requirements.txt")),
        # Buscar en el código sin rg ni grep: no cambia nada y no depende de nada.
        BuscarEnCodigoTool(raiz),
    ]
    # El equipo de agentes: Architect reparte, ellos analizan con sus herramientas.
    try:
        from ai_architect.agente.herramientas.equipo import herramientas_del_equipo

        base.extend(herramientas_del_equipo(raiz))
    except Exception:  # noqa: BLE001 - sin equipo se sigue con lo básico
        pass
    # La biblioteca: habilidades y especialistas, por tema, cuando hacen falta.
    try:
        from ai_architect.agente.herramientas.biblioteca import (
            herramientas_de_biblioteca,
        )

        base.extend(herramientas_de_biblioteca(raiz, bus=bus))
    except Exception:  # noqa: BLE001 - sin biblioteca se sigue con lo básico
        pass
    # Los canales configurados (celular, correo, WhatsApp) entran como herramientas.
    try:
        from ai_architect.agente.herramientas.canales import herramientas_de_canales

        base.extend(herramientas_de_canales())

        # El celular va por Telegram: si hay bot, se puede mandar.
        from ai_architect import canales

        if canales.configurado("telegram"):
            from ai_architect.agente.herramientas.celular import Celular, CelularLlamar

            base.extend([Celular(), CelularLlamar()])
    except Exception:  # noqa: BLE001 - sin canales se sigue igual
        pass
    if not con_skills and not con_mcp:
        return base

    extra: list[BaseTool] = []
    if con_skills:
        try:
            from ai_architect.agente import skills
            from ai_architect.agente.herramientas_base import ToolExecutor

            ejecutor = ToolExecutor(
                base,
                bus,
                interactive=True,
                confirm_callback=confirmar or (lambda _m: False),
            )
            extra.extend(skills.herramientas_skills(Path(raiz), ejecutor, bus))
        except Exception:  # noqa: BLE001 - sin skills se sigue igual
            pass
    if con_mcp:
        try:
            from ai_architect.agente import mcp

            remotas, clientes = mcp.herramientas_mcp()
            _clientes_mcp.extend(clientes)
            extra.extend(remotas)
        except Exception:  # noqa: BLE001 - sin MCP se sigue igual
            pass
    return base + extra


def nombres(herramientas: list[BaseTool]) -> list[str]:
    return [h.spec.name for h in herramientas]
