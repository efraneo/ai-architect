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
    avatar,
    changelog,
    configurar,
    conversar,
    crear,
    doctor,
    execute,
    improve,
    pide,
    review,
    tareas,
    voz,
)
from ai_architect.core.env_file import cargar_todo


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

    # Si `pide` puede elegirlo. La interfaz —abrir la cara, encender el
    # microfono, listar voces— no responde nada del repositorio, y dejarla
    # en el catalogo hizo que a "saluda a Rafa de mi parte" contestara
    # eligiendo `avatar`, que espera argumentos que `pide` no construye.
    elegible: bool = True


# `pide` va aparte de la tabla: es quien la usa, no uno de sus miembros.
# Meterlo dentro le dejaría elegirse a sí mismo.
COMANDOS: tuple[Comando, ...] = (
    Comando(
        "conversar",
        "Hablarle por el micrófono y que conteste (--si autoriza lo que escribe)",
        lambda a: conversar.run(a.project, si=a.si),
        elegible=False,
    ),
    Comando(
        "avatar",
        "Abrir el rostro (--texto para que lo diga en voz alta)",
        lambda a: avatar.run(decir=a.texto),
        elegible=False,
    ),
    Comando(
        "voz",
        "Ver qué voces hay y probarlas (--probar)",
        lambda a: voz.run(
            probar=a.probar, motor=a.motor, usar=a.usar, voz_piper=a.voz_piper
        ),
        elegible=False,
    ),
    Comando(
        "crear",
        "Preparar un documento, una tabla o una gráfica (--peticion)",
        lambda a: crear.run(a.peticion),
        requiere=(("peticion", "crear requires --peticion <qué quieres>"),),
    ),
    Comando(
        "configurar",
        "Guardar la clave del proveedor (--clave sk-...)",
        lambda a: configurar.run(clave=a.clave),
        elegible=False,
    ),
    Comando(
        "tareas",
        "Ver lo programado, o ejecutar lo que toque (--correr)",
        lambda a: tareas.run(
            correr_ahora=a.correr,
            project=a.project,
            registrar=a.registrar,
            desregistrar=a.desregistrar,
        ),
        elegible=False,
    ),
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
            apply=a.apply,
        ),
    ),
    Comando(
        "auto",
        "Varias mejoras en orden de prioridad",
        lambda a: auto.run(
            a.project,
            instructions=a.instructions,
            apply=a.apply,
        ),
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

# El despachador: recibe una frase y elige de la tabla de arriba.
PIDE = Comando(
    "pide",
    "Decir en una frase qué quieres y que elija el comando",
    lambda a: pide.run(
        a.project,
        frase=" ".join(a.frase or []),
        si=a.si,
        soy=a.soy,
        decir=a.decir,
        cara=a.cara,
    ),
)


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="ai-architect",
        description="QUANT AI Architect",
    )

    parser.add_argument(
        "command",
        choices=[comando.nombre for comando in COMANDOS] + [PIDE.nombre],
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
        "--correr",
        action="store_true",
        help="For tareas: run whatever is due right now",
    )

    parser.add_argument(
        "--registrar",
        action="store_true",
        help="For tareas: wake the architect from Windows Task Scheduler",
    )

    parser.add_argument(
        "--desregistrar",
        action="store_true",
        help="For tareas: remove it from Windows Task Scheduler",
    )

    parser.add_argument(
        "--clave",
        default="",
        help="For configurar: the provider API key to store",
    )

    parser.add_argument(
        "--peticion",
        default="",
        help="For crear: what document, table or chart you want",
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
        "--apply",
        action="store_true",
        help=(
            "For improve/auto: apply the patch, re-run the tests, and undo it "
            "if they get worse. Off by default: it modifies your files"
        ),
    )

    parser.add_argument(
        "--frase",
        nargs="+",
        default=None,
        help="For pide: what you want, in your own words",
    )

    parser.add_argument(
        "--usar",
        default="",
        choices=["", "piper", "openai", "windows"],
        help="For voz: remember this engine as your choice",
    )

    parser.add_argument(
        "--motor",
        default="",
        choices=["", "piper", "openai", "windows"],
        help="For voz: which engine to use, to compare how they sound",
    )

    parser.add_argument(
        "--voz-piper",
        default="",
        help="For voz: which Piper voice to keep (davefx, sharvard, ald, claude)",
    )

    parser.add_argument(
        "--probar",
        action="store_true",
        help="For voz: say a phrase out loud with the chosen engine",
    )

    parser.add_argument(
        "--decir",
        action="store_true",
        help="For pide: read the answer out loud",
    )

    parser.add_argument(
        "--cara",
        action="store_true",
        help="For pide: show the avatar; with --decir it moves its mouth",
    )

    parser.add_argument(
        "--texto",
        default="",
        help="For avatar: what the face should say out loud",
    )

    parser.add_argument(
        "--soy",
        default="",
        help="For pide: how you want to be addressed (asked once, remembered)",
    )

    parser.add_argument(
        "--si",
        action="store_true",
        help="For pide/conversar: authorise the commands that modify your files",
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
        # Una respuesta conversacional se lee entera; volcarle encima el
        # diccionario crudo la entierra. Con --json sale todo.
        if result.get("explanation"):
            print(result["explanation"])

            return

        for key, value in result.items():
            print(f"{key}: {value}")

        return

    print(result)


def main():

    parser = build_parser()

    args = parser.parse_args()

    # El `.env`: el de la sesión, el del proyecto que se analiza y el del
    # propio paquete. Mirar solo el directorio actual hacía que la clave
    # dependiera de desde dónde se llame — un acceso directo o un `.cmd`
    # desde otra carpeta y el proveedor contestaba `not_configured`
    # teniendo la clave a dos carpetas. Lo ya exportado manda sobre todo.
    cargar_todo(getattr(args, "project", None))

    comando = PIDE if args.command == PIDE.nombre else POR_NOMBRE.get(args.command)

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
