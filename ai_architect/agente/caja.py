"""La caja de herramientas que Architect lleva a un repositorio.

Todas las herramientas quedan acotadas al repositorio: leer y escribir solo dentro de él, la
consola arranca en él, y git actúa sobre él. Las que modifican algo piden confirmación al
``ToolExecutor``; sin permiso, el agente recibe una negativa y propone en vez de tocar.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from ai_architect.agente.herramientas.escribir import FileWriteTool
from ai_architect.agente.herramientas.git import (
    GitCommitTool,
    GitDiffTool,
    GitLogTool,
    GitStatusTool,
)
from ai_architect.agente.herramientas.leer import FileReadTool
from ai_architect.agente.herramientas.parche import ApplyPatchTool
from ai_architect.agente.herramientas.shell import ShellExecTool
from ai_architect.agente.herramientas_base import BaseTool, ToolSpec

# Nombres de las herramientas que cambian el repositorio o ejecutan cosas.
ESCRIBEN = frozenset({"file_write", "apply_patch", "shell_exec", "git_commit"})


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


def herramientas_para(repositorio: Path) -> list[BaseTool]:
    raiz = str(Path(repositorio).resolve())
    return [
        FileReadTool(allowed_dirs=[raiz]),
        EscribirConPermiso(allowed_dirs=[raiz]),
        ParcheConPermiso(),
        ShellConPermiso(),
        GitStatusTool(),
        GitDiffTool(),
        GitLogTool(),
        CommitConPermiso(),
    ]


def nombres(herramientas: list[BaseTool]) -> list[str]:
    return [h.spec.name for h in herramientas]
