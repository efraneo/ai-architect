"""
=========================================================
Configurar

El primer arranque, en otro ordenador.
=========================================================

Instalado limpio y ejecutado sin clave, el arquitecto contestaba esto:

    el proveedor falló: OPENAI_API_KEY is not configured.

Un error en inglés, con el nombre de una variable de entorno, y ni una
palabra sobre qué hacer. Quien acaba de instalarlo no sabe qué es una
variable de entorno ni tiene por qué saberlo.

Esto lo arregla por los dos lados: hay un comando que la guarda, y el
mensaje de "no puedo" pasa a decir exactamente qué escribir.

**Dónde se guarda.** En ``~/.ai_architect/.env``, la carpeta del usuario,
no la del proyecto. La clave es de la persona y no cambia según en qué
repositorio esté trabajando; guardarla junto al código además invita a que
acabe en un commit.
"""

from __future__ import annotations

import os
import stat
from typing import Any

from ai_architect.core import perfil
from ai_architect.core.env_file import CARPETA_USUARIO

ARCHIVO = CARPETA_USUARIO / ".env"

# Lo que hace falta para que responda. Lo demás es opcional.
CLAVES = {
    "OPENAI_API_KEY": "OpenAI — responde, habla y transcribe",
    "ANTHROPIC_API_KEY": "Claude — proveedor alternativo",
}


def run(clave: str = "", proveedor: str = "OPENAI_API_KEY") -> dict[str, Any]:
    """Guarda la clave, o dice cómo conseguirla si no se le pasa ninguna."""
    if not clave.strip():
        return {
            "success": True,
            "configured": esta_configurado(),
            "explanation": _instrucciones(),
        }

    if proveedor not in CLAVES:
        return {
            "success": False,
            "error": f"no conozco '{proveedor}'. Son: {', '.join(CLAVES)}",
        }

    guardada = guardar(proveedor, clave.strip())

    if not guardada:
        return {"success": False, "error": f"no pude escribir en {ARCHIVO}"}

    return {
        "success": True,
        "path": str(ARCHIVO),
        "explanation": (
            f"{perfil.encabezar()} Clave guardada en {ARCHIVO}.\n\n"
            "Ya puedes pedirme lo que quieras:\n"
            '    architect pide "cómo está el proyecto"\n'
            "    architect conversar"
        ),
    }


def guardar(nombre: str, valor: str) -> bool:
    """Escribe la clave sin tocar lo demás que hubiera en el archivo."""
    try:
        ARCHIVO.parent.mkdir(parents=True, exist_ok=True)

        lineas = []

        if ARCHIVO.is_file():
            lineas = [
                linea
                for linea in ARCHIVO.read_text(encoding="utf-8").splitlines()
                if not linea.strip().startswith(f"{nombre}=")
            ]

        lineas.append(f"{nombre}={valor}")

        ARCHIVO.write_text("\n".join(lineas) + "\n", encoding="utf-8")

        # Solo el dueño. En Windows los permisos POSIX no hacen gran cosa,
        # pero en Linux y macOS esto es la diferencia entre una clave
        # privada y una que lee cualquiera con cuenta en la máquina.
        ARCHIVO.chmod(stat.S_IRUSR | stat.S_IWUSR)

    except OSError:
        return False

    return True


def esta_configurado() -> bool:
    from ai_architect.voz.hablar import _asegurar_entorno

    _asegurar_entorno()

    return any(os.getenv(nombre) for nombre in CLAVES)


def _instrucciones() -> str:
    if esta_configurado():
        return (
            f"{perfil.encabezar()} Ya tengo clave, todo listo.\n\n"
            "Si quieres cambiarla:\n"
            "    architect configurar --clave sk-..."
        )

    return (
        f"{perfil.saludo()}. Me falta una clave para poder pensar.\n\n"
        "  1. Entra en platform.openai.com/api-keys y crea una.\n"
        "  2. Pégala aquí:\n\n"
        "         architect configurar --clave sk-...\n\n"
        f"Se guarda en {ARCHIVO}, solo para ti, y no se sube a ningún sitio.\n"
        "Lo que no necesita clave —analizar, revisar, los agentes— ya funciona."
    )


def falta_la_clave() -> str:
    """Lo que se dice cuando algo necesita proveedor y no hay.

    Se usa desde donde falle, en vez de dejar salir el error del proveedor:
    "OPENAI_API_KEY is not configured" es correcto y no ayuda a nadie.
    """
    return (
        "Me falta la clave del proveedor para esto. "
        "Ponla con: architect configurar --clave sk-... "
        "Mientras tanto puedo analizar, revisar y pasar los agentes, "
        "que no la necesitan."
    )
