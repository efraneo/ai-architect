"""
=========================================================
Los agentes de la vida diaria

Agenda, hogar, investigación y sistema: revisan el entorno, no el repositorio.
=========================================================

Cada uno sabe decir cómo está su parte (qué falta, qué hay pendiente) y
obedece órdenes por ``agents.ordenes`` (recordar, encender, clima, abrir…).
No entran en ``AgentManager.inspect`` (eso es del repositorio) pero sí en la
herramienta ``equipo`` y como ``agente_<tema>``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .base_agent import BaseAgent


class AgendaAgent(BaseAgent):
    name = "Agenda Agent"

    def run(self, context):
        return self.review(context)

    def review(self, project: str) -> dict[str, Any]:  # noqa: ARG002
        from ai_architect import agenda

        ahora = datetime.now()
        hoy = agenda.pendientes(ahora.date())
        todos = agenda.pendientes()
        findings: list[dict[str, Any]] = []

        for a in hoy[:5]:
            findings.append(
                {
                    "type": "recordatorio",
                    "issue": f"{a['texto']} a las {str(a['cuando'])[11:16]}",
                }
            )

        return {
            "agent": self.name,
            "status": "OK",
            "momento": agenda.momento_del_dia(ahora),
            "hoy": len(hoy),
            "pendientes": len(todos),
            "contexto": agenda.contexto(ahora),
            "findings": findings,
        }

    def capabilities(self) -> list[str]:
        return ["agenda", "recordatorios por voz", "contexto del dia", "que toca hoy"]


class HogarAgent(BaseAgent):
    name = "Hogar Agent"

    def run(self, context):
        return self.review(context)

    def review(self, project: str) -> dict[str, Any]:  # noqa: ARG002
        from ai_architect.canales import hogar

        informe: dict[str, Any] = {"agent": self.name, "status": "OK"}
        findings: list[dict[str, Any]] = []
        informe["configurado"] = hogar.configurado()

        if not hogar.configurado():
            findings.append(
                {
                    "type": "hogar",
                    "issue": "sin Home Assistant configurado (falta "
                    + ", ".join(hogar.que_falta())
                    + "): di «configura el hogar»",
                }
            )
            informe["findings"] = findings

            return informe

        try:
            lista = hogar.dispositivos()

        except Exception as e:  # noqa: BLE001 - sin conexión se cuenta
            findings.append(
                {"type": "hogar", "issue": f"no llego a Home Assistant: {e}"}
            )
            informe["findings"] = findings

            return informe

        informe["dispositivos"] = len(lista)
        informe["encendidos"] = [d["nombre"] for d in lista if d["estado"] == "on"][:20]
        sin_conexion = [d["nombre"] for d in lista if d["estado"] == "unavailable"]

        for nombre in sin_conexion[:5]:
            findings.append({"type": "sin conexion", "issue": f"{nombre} no responde"})

        informe["findings"] = findings

        return informe

    def capabilities(self) -> list[str]:
        return [
            "hogar",
            "luces y enchufes",
            "persianas y puertas",
            "sensores",
            "home assistant",
        ]


class InvestigacionAgent(BaseAgent):
    name = "Investigación Agent"

    def run(self, context):
        return self.review(context)

    def review(self, project: str) -> dict[str, Any]:  # noqa: ARG002
        from ai_architect import investigar
        from ai_architect.canales import correo

        informe: dict[str, Any] = {"agent": self.name, "status": "OK"}
        findings: list[dict[str, Any]] = []
        informe["ciudad"] = investigar.ciudad()
        informe["lee_correo"] = correo.puede_leer()

        if not informe["ciudad"]:
            findings.append(
                {
                    "type": "ciudad",
                    "issue": "no sé en qué ciudad estás: di «recuerda que vivo en …» (clima y lluvia)",
                }
            )

        if not informe["lee_correo"]:
            findings.append(
                {
                    "type": "correo",
                    "issue": "sin IMAP no puedo avisarte de correos urgentes (CORREO_IMAP_HOST)",
                }
            )

        informe["findings"] = findings

        return informe

    def capabilities(self) -> list[str]:
        return [
            "investigacion",
            "clima y lluvia",
            "noticias",
            "correo urgente",
            "avisos proactivos",
        ]


class SistemaAgent(BaseAgent):
    name = "Sistema Agent"

    def run(self, context):
        return self.review(context)

    def review(self, project: str) -> dict[str, Any]:  # noqa: ARG002
        import platform
        import shutil

        from ai_architect.commands import abrir
        from ai_architect.office import word

        informe: dict[str, Any] = {"agent": self.name, "status": "OK"}
        findings: list[dict[str, Any]] = []
        informe["sistema"] = f"{platform.system()} {platform.release()}"
        informe["programas_conocidos"] = sorted(abrir.PROGRAMAS)[:40]
        informe["word"] = word.disponible()

        uso = shutil.disk_usage(project or ".")
        libre_gb = uso.free / 1e9
        informe["disco_libre_gb"] = round(libre_gb, 1)

        if libre_gb < 5:
            findings.append(
                {
                    "type": "disco",
                    "issue": f"quedan {libre_gb:.1f} GB libres en el disco",
                }
            )

        if not informe["word"]:
            findings.append(
                {"type": "word", "issue": "Word no está disponible para dictar"}
            )

        informe["findings"] = findings

        return informe

    def capabilities(self) -> list[str]:
        return [
            "sistema",
            "abrir programas",
            "archivos y carpetas",
            "word",
            "ventana",
            "disco",
        ]
