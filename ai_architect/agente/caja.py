"""La caja de herramientas que Architect lleva a un repositorio.

Todas las herramientas quedan acotadas al repositorio: leer y escribir solo dentro de él, la
consola arranca en él, y git actúa sobre él. Las que modifican algo piden confirmación al
``ToolExecutor``; sin permiso, el agente recibe una negativa y propone en vez de tocar.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

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
        "instalar",
        "celular_llamar",
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
    pass


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
    ]
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
