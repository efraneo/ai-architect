"""
=========================================================
Approval Engine

Qué se deja pasar sin que nadie mire.
=========================================================
"""

from __future__ import annotations

from typing import Any

# El motor de decisión de este proyecto devuelve la confianza en 0-1
# (``0.73``). Este módulo la comparaba contra ``90``, así que **nada se
# aprobaba nunca**: 0.73 >= 90 es falso siempre. Como nadie lo llamaba, el
# desajuste no se notó.
CONFIANZA_MINIMA = 0.75

RIESGOS_VETADOS = {"CRITICAL", "CRÍTICO", "HIGH"}


class ApprovalEngine:
    def __init__(
        self,
        confianza_minima: float = CONFIANZA_MINIMA,
    ) -> None:
        self.confianza_minima = confianza_minima

    def approve(
        self,
        execution: dict[str, Any],
    ) -> bool:
        """¿Se puede dar por bueno esto sin que lo mire una persona?

        Las tres condiciones son excluyentes y el fallo va siempre hacia el
        "no": lo que no se sabe, no se aprueba.
        """
        if not execution.get("tests_ok", False):
            return False

        riesgo = str(execution.get("risk", "LOW")).upper()

        if riesgo in RIESGOS_VETADOS:
            return False

        confianza = execution.get("confidence", 0)

        if not isinstance(confianza, (int, float)) or isinstance(confianza, bool):
            return False

        return float(confianza) >= self.confianza_minima

    def motivo(
        self,
        execution: dict[str, Any],
    ) -> str:
        """Por qué no se aprobó. Un ``False`` a secas no sirve para actuar."""
        if not execution.get("tests_ok", False):
            return "las pruebas no pasaron"

        riesgo = str(execution.get("risk", "LOW")).upper()

        if riesgo in RIESGOS_VETADOS:
            return f"riesgo {riesgo}"

        confianza = execution.get("confidence", 0)

        if not isinstance(confianza, (int, float)) or isinstance(confianza, bool):
            return "sin confianza declarada"

        if float(confianza) < self.confianza_minima:
            return f"confianza {float(confianza):.2f} < {self.confianza_minima}"

        return "aprobado"
