"""
=========================================================
Voz y Canales Agent

Si Architect puede oír, hablar, mandar el celular, el correo y Word: lo que
falta y cómo se consigue.
=========================================================
"""

from __future__ import annotations

from typing import Any

from .base_agent import BaseAgent


class VozAgent(BaseAgent):
    name = "Voz y Canales Agent"

    def run(self, context):
        return self.review(context)

    def review(
        self, project: str
    ) -> dict[str, Any]:  # noqa: ARG002 - no mira el repositorio
        findings: list[dict[str, Any]] = []
        estado: dict[str, Any] = {"agent": self.name, "status": "OK"}

        # --- oído y voz ------------------------------------------------------------
        try:
            from ai_architect.voz import escuchar, hablar

            motores = hablar.motores()
            estado["oido"] = "whisper" if escuchar.disponible() else "navegador"
            estado["voces"] = {n: bool(d.get("disponible")) for n, d in motores.items()}

            if not any(estado["voces"].values()):
                findings.append(
                    {
                        "type": "voz",
                        "issue": "no hay ninguna voz: instala Piper o pon OPENAI_API_KEY",
                    }
                )

            if not escuchar.disponible():
                findings.append(
                    {
                        "type": "oido",
                        "issue": "sin OPENAI_API_KEY oye con el reconocedor de Chrome (peor en español)",
                    }
                )

        except Exception as e:  # noqa: BLE001 - se cuenta
            findings.append({"type": "voz", "issue": f"no pude comprobar la voz: {e}"})

        # --- ventana flotante ------------------------------------------------------
        try:
            from ai_architect.commands import avatar

            estado["ventana_flotante"] = avatar.hay_ventana_flotante()

            if not estado["ventana_flotante"]:
                findings.append(
                    {
                        "type": "ventana",
                        "issue": "sin pywebview no hay ventana flotante (pip install pywebview)",
                    }
                )

        except Exception as e:  # noqa: BLE001
            findings.append({"type": "ventana", "issue": str(e)})

        # --- canales -----------------------------------------------------------------
        try:
            from ai_architect import canales

            situacion = canales.estado()
            estado["canales"] = {c: d["configurado"] for c, d in situacion.items()}

            for canal, datos in situacion.items():
                if not datos["configurado"]:
                    findings.append(
                        {
                            "type": f"canal {canal}",
                            "issue": f"sin configurar (falta {', '.join(datos['falta'])})",
                        }
                    )

        except Exception as e:  # noqa: BLE001
            findings.append({"type": "canales", "issue": str(e)})

        # --- Word ---------------------------------------------------------------------
        try:
            from ai_architect.office import word

            estado["word"] = word.disponible()

            if not estado["word"]:
                findings.append(
                    {"type": "word", "issue": "sin Word o sin pywin32 no hay dictado"}
                )

        except Exception as e:  # noqa: BLE001
            findings.append({"type": "word", "issue": str(e)})

        # --- memoria y aprendizaje -------------------------------------------------------
        try:
            from ai_architect import autoreparacion
            from ai_architect.agente import memoria

            estado["hechos_en_memoria"] = len(memoria.hechos())
            pendiente = autoreparacion.pendiente()
            estado["reparador"] = autoreparacion.reparador()

            if pendiente:
                findings.append(
                    {
                        "type": "pendiente",
                        "issue": f"hay una {pendiente['comando']} esperando tu «adelante»: {pendiente['frase'][:80]}",
                    }
                )

        except Exception as e:  # noqa: BLE001
            findings.append({"type": "memoria", "issue": str(e)})

        estado["findings"] = findings

        return estado

    def capabilities(self) -> list[str]:
        return [
            "voz",
            "oido (whisper o navegador)",
            "voces disponibles",
            "ventana flotante",
            "canales (telegram, correo, whatsapp)",
            "dictado a word",
            "memoria y averias pendientes",
        ]
