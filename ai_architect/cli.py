"""
=========================================================
QUANT AI Architect CLI
=========================================================

Los comandos viven en una tabla, no en una cadena de ``elif``.

Antes cada comando nuevo obligaba a tocar **tres sitios**: la lista de
``choices``, la cadena de ``elif`` y sus banderas. Olvidarse de uno no daba
error: el comando existía y no hacía nada, o hacía lo del anterior. Pasó de
cinco comandos a ocho durante el trabajo de conexión, y la complejidad del
módulo llegó a 15.

Ahora se añade un `Comando` a ``COMANDOS`` y ya está: las ``choices`` salen
de ahí.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ai_architect.commands import (
    agents,
    analyze,
    auto,
    changelog,
    doctor,
    execute,
    improve,
    review,
)


@dataclass(frozen=True)
class Comando:
    """Un comando del CLI: cómo se llama, qué corre y qué exige.

    ``requiere`` son las banderas sin las que el comando no tiene sentido.
    Se comprueban antes de ejecutar nada, y el mensaje sale del propio
    comando en vez de repetirse a mano en cada rama.
    """

    nombre: str

    ayuda: str

    ejecutar: Callable[[argparse.Namespace], Any]

    requiere: tuple[tuple[str, str], ...] = field(default=())


COMANDOS: tuple[Comando, ...] = (
    Comando(
        "doctor",
        "Comprobar el entorno: proveedor, agentes y git",
        lambda a: doctor.run(),
    ),
    Comando(
        "analyze",
        "Analizar la estructura del repositorio",
        lambda a: analyze.run(a.project),
    ),
    Comando(
        "review",
        "Revisar el código y puntuarlo",
        lambda a: review.run(a.project),
    ),
    Comando(
        "agents",
        "Pasar los agentes estáticos (--ai añade los de IA)",
        lambda a: agents.run(a.project, ai=a.ai),
    ),
    Comando(
        "changelog",
        "Armar la entrada de changelog desde el historial de git",
        lambda a: changelog.run(
            a.project,
            version=a.version_name,
            write=a.write,
            since=a.since,
        ),
    ),
    Comando(
        "improve",
        "Generar un parche de mejora (requiere clave de proveedor)",
        lambda a: improve.run(
            a.project,
            file=a.file,
            instruction=a.instruction,
        ),
    ),
    Comando(
        "auto",
        "Varias mejoras en orden de prioridad",
        lambda a: auto.run(a.project, instructions=a.instructions),
        requiere=(("instructions", "auto requires --instructions <one> <two> ..."),),
    ),
    Comando(
        "execute",
        "Aplicar un parche (--dry-run para validarlo sin tocar nada)",
        lambda a: execute.run(
            project=a.project,
            patch=a.patch,
            dry_run=a.dry_run,
        ),
        requiere=(("patch", "execute requires --patch <patch_file>"),),
    ),
)

POR_NOMBRE = {comando.nombre: comando for comando in COMANDOS}


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="ai-architect",
        description="QUANT AI Architect",
    )

    parser.add_argument(
        "command",
        choices=[comando.nombre for comando in COMANDOS],
        help="; ".join(f"{c.nombre}: {c.ayuda}" for c in COMANDOS),
    )

    parser.add_argument(
        "project",
        nargs="?",
        default=".",
        help="Project directory",
    )

    parser.add_argument(
        "--file",
        default=None,
        help="Target file for improve command",
    )

    parser.add_argument(
        "--patch",
        default=None,
        help="Patch file for execute command",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate an execution patch without modifying files",
    )

    parser.add_argument(
        "--instruction",
        default="Improve code quality",
        help="Instruction for improve command",
    )

    parser.add_argument(
        "--instructions",
        nargs="+",
        default=None,
        help="For auto: several instructions, most important first",
    )

    parser.add_argument(
        "--version-name",
        default="",
        help="For changelog: the name of this version",
    )

    parser.add_argument(
        "--since",
        default=None,
        help="For changelog: reference to count from (default: latest tag)",
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help="For changelog: write CHANGELOG.md instead of only showing it",
    )

    parser.add_argument(
        "--ai",
        action="store_true",
        help="For agents: also run the AI agents (five provider calls)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print result as JSON",
    )

    return parser


def print_result(
    result,
    as_json: bool,
):

    if as_json:
        print(
            json.dumps(
                result,
                indent=4,
                default=str,
            )
        )

        return

    if isinstance(result, dict):
        for key, value in result.items():
            print(f"{key}: {value}")

        return

    print(result)


def main():

    parser = build_parser()

    args = parser.parse_args()

    comando = POR_NOMBRE.get(args.command)

    if comando is None:  # argparse ya lo impide; queda por si cambian las choices
        parser.error("Unknown command.")

    for bandera, mensaje in comando.requiere:
        if not getattr(args, bandera, None):
            parser.error(mensaje)

    print_result(
        comando.ejecutar(args),
        args.json,
    )


if __name__ == "__main__":
    sys.exit(main())
