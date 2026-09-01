"""
=========================================================
Consensus Engine

Once informes, un veredicto.
=========================================================
"""

from __future__ import annotations

from typing import Any

# Lo que un agente puede decir de sí mismo. Cualquier otra cosa se toma por
# buena: la mayoría reporta ``"OK"``, y un agente que no dice nada no es un
# fallo.
FALLO = {"FAILED", "ERROR"}

AVISO = {"WARNING", "WARN"}


class ConsensusEngine:
    def evaluate(
        self,
        reports: dict[str, Any],
    ) -> dict[str, Any]:
        """Resume lo que dijeron todos los agentes.

        Antes solo miraba ``"FAILED"`` y ``"WARNING"``. Los agentes de este
        proyecto reportan ``{"status": "error"}`` cuando revientan, así que
        **un agente caído contaba como éxito**: el consenso aprobaba una
        inspección que no se había podido hacer.
        """
        avisos = 0
        fallos = 0
        exitos = 0

        caidos: list[str] = []
        con_hallazgos: list[str] = []

        for nombre, report in reports.items():
            if not isinstance(report, dict):
                continue

            estado = str(report.get("status", "OK")).upper()

            if estado in FALLO:
                fallos += 1
                caidos.append(nombre)

            elif estado in AVISO:
                avisos += 1

            else:
                exitos += 1

            if report.get("findings"):
                con_hallazgos.append(nombre)

        return {
            "approved": fallos == 0 and not con_hallazgos,
            "success": exitos,
            "warnings": avisos,
            "failures": fallos,
            "failed_agents": caidos,
            "agents_with_findings": con_hallazgos,
            "total_agents": len(reports),
        }
