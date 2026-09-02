"""
=========================================================
Voz

Qué voces hay, y cómo suenan.
=========================================================

Antes de ponerle voz a nada conviene saber qué se tiene. Este comando lo
dice sin adornos: cuál se usaría, cuáles faltan, y qué habría que hacer para
la que se quería.

Sobre el equipo donde se escribió esto, Windows solo tenía voces femeninas
en español. Decir "listo, ya tienes voz masculina latina" habría sido mentir
en lo primero que se nota.
"""

from __future__ import annotations

from typing import Any

from ai_architect.core import perfil
from ai_architect.voz import hablar as motor_de_voz


def run(
    probar: bool = False,
    texto: str = "",
    motor: str = "",
    usar: str = "",
    voz_piper: str = "",
) -> dict:
    """Informa de las voces disponibles. Con ``probar``, dice una frase.

    Con ``motor`` se prueba una concreta, para poder comparar cómo suenan
    antes de decidir cuál usar.
    """
    motores = motor_de_voz.motores()

    if voz_piper:
        return _elegir_voz_de_piper(voz_piper)

    if usar:
        if not motores.get(usar, {}).get("disponible"):
            return {
                "success": False,
                "explanation": f"'{usar}' no está disponible en este equipo.",
            }

        perfil.preferir_voz(usar)

        return {
            "success": True,
            "chosen": usar,
            "explanation": (
                f"{perfil.encabezar()} Me quedo con {usar}. "
                "A partir de ahora es la que uso."
            ),
        }

    elegido = motor_de_voz.elegir(motor)

    lineas = ["Voces disponibles:"]

    for nombre, datos in motores.items():
        marca = "->" if nombre == elegido else "  "
        estado = "sí" if datos["disponible"] else "no"

        detalle = datos["nota"]

        if nombre == "piper" and datos["voz"]:
            detalle = f"{datos['voz']} — {detalle}"

        lineas.append(f"  {marca} {nombre:8} {estado:3} {detalle}")

    if not elegido:
        lineas.append("")
        lineas.append("Ninguna disponible. La más fácil: instala una voz de")
        lineas.append("Windows en Configuración > Hora e idioma > Voz.")

    resultado: dict[str, Any] = {
        "success": True,
        "engines": motores,
        "chosen": elegido,
        "explanation": "\n".join(lineas),
    }

    if probar and elegido:
        frase = texto or f"{perfil.encabezar()} Soy el arquitecto. Ya me escuchas."

        dicho = motor_de_voz.hablar(frase, motor)

        resultado["spoken"] = dicho
        resultado["explanation"] += f"\n\nProbando con {dicho['motor'] or 'nada'}: " + (
            "dicho." if dicho["hablado"] else dicho["motivo"]
        )

    return resultado


def _elegir_voz_de_piper(nombre: str) -> dict:
    """Cuál de las voces de Piper. Son cuatro y suenan muy distinto.

    Se admite el nombre corto —`davefx`, `sharvard`, `ald`— porque nadie
    quiere teclear `es_ES-davefx-medium.onnx` para cambiar de voz.
    """
    disponibles = [
        v.name for v in sorted(motor_de_voz.CARPETA_VOCES.glob("*.onnx")) if v.is_file()
    ]

    elegida = next((v for v in disponibles if nombre.lower() in v.lower()), "")

    if not elegida:
        return {
            "success": False,
            "available": disponibles,
            "explanation": (
                f"No tengo ninguna voz que se llame '{nombre}'. "
                "Tengo estas: " + ", ".join(disponibles or ["ninguna"])
            ),
        }

    perfil.preferir_voz("piper")
    perfil.preferir_voz_piper(elegida)

    return {
        "success": True,
        "chosen": elegida,
        "explanation": (
            f"{perfil.encabezar()} Me quedo con {elegida}, de Piper. "
            "Es local y no cuesta nada."
        ),
    }
