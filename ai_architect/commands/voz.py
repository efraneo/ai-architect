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
) -> dict:
    """Informa de las voces disponibles. Con ``probar``, dice una frase."""
    motores = motor_de_voz.motores()

    elegido = motor_de_voz.elegir()

    lineas = ["Voces disponibles:"]

    for nombre, datos in motores.items():
        marca = "->" if nombre == elegido else "  "
        estado = "sí" if datos["disponible"] else "no"

        lineas.append(f"  {marca} {nombre:8} {estado:3} {datos['nota']}")

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

        dicho = motor_de_voz.hablar(frase)

        resultado["spoken"] = dicho
        resultado["explanation"] += f"\n\nProbando con {dicho['motor'] or 'nada'}: " + (
            "dicho." if dicho["hablado"] else dicho["motivo"]
        )

    return resultado
