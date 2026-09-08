"""Cómo se cuenta el resultado de un comando: la frase que se lee y el panel que se enseña.

Sin llamadas al modelo: los resultados son diccionarios conocidos. ``pide`` reexporta estos nombres.
"""

from __future__ import annotations

from typing import Any


def explicar(nombre: str, resultado: Any) -> str:
    """El resultado, en una frase que se entienda.

    Se arma aquí y no con otra llamada al modelo: los resultados son
    diccionarios que controlamos, así que explicarlos no necesita IA — y una
    segunda llamada duplicaría el coste para inventar lo que ya sabemos.
    """
    if not isinstance(resultado, dict):
        return str(resultado)

    if not resultado.get("success", True):
        return f"No salió: {resultado.get('error', 'sin motivo')}"

    if nombre == "doctor":
        estado = resultado.get("status", "?")
        partes = [
            f"{clave}: {(valor or {}).get('status', '?')}"
            for clave, valor in (resultado.get("components") or {}).items()
            if isinstance(valor, dict)
        ]
        return f"El entorno está {estado}. " + ", ".join(partes)

    if nombre == "agents":
        veredicto = resultado.get("verdict") or {}
        con = veredicto.get("agents_with_findings") or []
        return (
            f"{veredicto.get('total_agents', 0)} agentes revisaron el proyecto. "
            f"{resultado.get('total_findings', 0)} hallazgos"
            + (f", en: {', '.join(con)}." if con else ", ninguno.")
        )

    if nombre == "review":
        return (
            f"Puntuación {resultado.get('score')}, "
            f"{resultado.get('total_issues', 0)} incidencias. "
            + ("Aprobado." if resultado.get("approved") else "No aprobado.")
        )

    if nombre == "analyze":
        resumen = resultado.get("summary") or {}
        return (
            f"{resumen.get('python_files', 0)} archivos Python, "
            f"{resumen.get('total_functions', 0)} funciones, "
            f"complejidad media {resumen.get('average_complexity', 0)}."
        )

    if nombre == "improve":
        return _explicar_mejora(resultado)

    if nombre == "auto":
        return (
            f"{resultado.get('executed', 0)} de {resultado.get('total_tasks', 0)} "
            f"tareas ejecutadas, {resultado.get('approved', 0)} aprobadas."
        )

    if nombre == "changelog":
        return (
            f"Versión {resultado.get('version')}: "
            f"{resultado.get('total_changes', 0)} cambios desde "
            f"{resultado.get('since')}. "
            + (
                "Escrito en CHANGELOG.md."
                if resultado.get("written")
                else "No escrito."
            )
        )

    return "Hecho."


def _explicar_mejora(resultado: dict[str, Any]) -> str:
    """Lo de `improve` merece detalle: dice si tus archivos cambiaron."""
    arbol = {
        "untouched": "No toqué ningún archivo tuyo.",
        "modified": "El cambio quedó aplicado. Revísalo.",
        "restored": "Lo apliqué, rompía las pruebas, y lo deshice.",
        "dirty": "ATENCIÓN: rompía las pruebas y no se pudo deshacer.",
    }.get(str(resultado.get("working_tree", "")), "")

    decision = resultado.get("decision") or {}

    return (
        f"Parche de {resultado.get('files', 0)} archivo(s). "
        f"Decisión: {decision.get('decision', '?')} "
        f"(score {(decision.get('metrics') or {}).get('score', '?')}). " + arbol
    )


def panel(nombre: str, resultado: Any) -> dict[str, Any] | None:
    """Lo que se ensena en la ventana flotante, si hay algo que ensenar.

    Oir "puntuacion 99.26, 41 incidencias" y que se quede en el aire no es
    lo mismo que verlo y poder volver a mirarlo. Se manda ya masticado
    porque la pagina no tiene por que saber la forma de cada resultado.
    """
    if not isinstance(resultado, dict) or not resultado.get("success", True):
        return None

    if nombre == "review":
        return {
            "tipo": "puntuacion",
            "titulo": "Revision",
            "valor": resultado.get("score"),
            "incidencias": resultado.get("issues") or resultado.get("total_issues"),
            "veredicto": resultado.get("verdict") or resultado.get("status"),
        }

    if nombre == "agents":
        veredicto = resultado.get("verdict") or {}

        return {
            "tipo": "hallazgos",
            "titulo": "Agentes",
            "total": resultado.get("total_findings"),
            "agentes": veredicto.get("total_agents"),
            "con_hallazgos": list(veredicto.get("agents_with_findings") or []),
        }

    if nombre == "doctor":
        return {
            "tipo": "estado",
            "titulo": "Entorno",
            "estado": resultado.get("status"),
            "componentes": {
                clave: (valor or {}).get("status")
                for clave, valor in (resultado.get("components") or {}).items()
            },
        }

    if nombre == "analyze":
        return {
            "tipo": "estructura",
            "titulo": "Estructura",
            "archivos": resultado.get("total_files") or resultado.get("files"),
            "lineas": resultado.get("total_lines") or resultado.get("lines"),
            "funciones": resultado.get("total_functions") or resultado.get("functions"),
        }

    if nombre == "changelog":
        return {
            "tipo": "texto",
            "titulo": "Changelog",
            "cuerpo": str(resultado.get("changelog") or resultado.get("entry") or "")[
                :4000
            ],
        }

    if nombre in ("improve", "auto"):
        return {
            "tipo": "texto",
            "titulo": "Mejora",
            "cuerpo": str(resultado.get("diff") or "")[:4000],
        }

    return None
