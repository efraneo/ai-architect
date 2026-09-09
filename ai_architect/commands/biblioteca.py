"""La biblioteca por voz: instalarla, preguntarle qué tiene y delegar.

    tú   ¿Qué habilidades tienes para seguridad en Django?
    tú   ¿Qué especialistas tienes?
    tú   Usa la habilidad tdd-workflow y añade pruebas al módulo de voz.
    tú   Que el especialista de seguridad revise el proyecto.
    tú   Instala la biblioteca. / Actualiza la biblioteca.

Las dos últimas formas delegan en el agente ``hacer`` con una orden que ya
nombra la herramienta (``usar_habilidad`` o ``especialista``): así no se
adivina nada.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect.core.texto import sin_adornos

INSTALAR = (
    "instala la biblioteca",
    "instala tu biblioteca",
    "descarga la biblioteca",
    "instala las habilidades",
    "instala los especialistas",
    "instala la biblioteca de habilidades",
)

ACTUALIZAR = (
    "actualiza la biblioteca",
    "actualiza tu biblioteca",
    "actualiza las habilidades",
    "actualiza los especialistas",
)

CUANTAS = (
    "cuantas habilidades tienes",
    "cuantos especialistas tienes",
    "que hay en tu biblioteca",
    "que tienes en la biblioteca",
    "estado de la biblioteca",
    "que especialistas tienes",
    "que habilidades tienes",
    "lista tus habilidades",
    "lista tus especialistas",
)

BUSCAR = re.compile(
    r"^(?:que|cuales|cuantas|cuantos)\s+(?P<tipo>habilidades|especialistas|reglas|recetas|skills|agentes)\s+"
    r"(?:tienes|hay|conoces)\s+(?:para|de|sobre|en)\s+(?P<tema>.+?)\??$"
)

USAR = re.compile(
    r"^(?:usa|aplica|sigue|utiliza)\s+la\s+(?:habilidad|skill)\s+(?P<nombre>[\w-]+)\s*(?:y|para|:|,)?\s*(?P<tarea>.*)$",
    re.IGNORECASE,
)

DELEGAR = re.compile(
    r"^(?:que|qué|dile a|dile al|pidele a|pídele a|pidele al|pídele al|manda a|manda al|llama a|llama al|usa)\s+"
    r"(?:el\s+|al\s+|la\s+)?(?:especialista|agente|revisor|experto)\s+"
    r"(?:de\s+|en\s+)?(?P<nombre>[\w-]+)\s+(?:que\s+|para\s+que\s+|y\s+)?(?P<tarea>.+)$",
    re.IGNORECASE,
)

TEMAS_A_ESPECIALISTA = {
    "seguridad": "security-reviewer",
    "security": "security-reviewer",
    "rendimiento": "performance-optimizer",
    "python": "python-reviewer",
    "typescript": "typescript-reviewer",
    "javascript": "typescript-reviewer",
    "react": "react-reviewer",
    "base de datos": "database-reviewer",
    "datos": "database-reviewer",
    "pruebas": "tdd-guide",
    "planificacion": "planner",
    "arquitectura": "architect",
    "documentacion": "doc-updater",
    "limpieza": "refactor-cleaner",
    "errores": "silent-failure-hunter",
    "accesibilidad": "a11y-architect",
    "seo": "seo-specialist",
    "marketing": "marketing-agent",
    "redes": "network-architect",
    "go": "go-reviewer",
    "rust": "rust-reviewer",
    "java": "java-reviewer",
    "kotlin": "kotlin-reviewer",
    "swift": "swift-reviewer",
    "php": "php-reviewer",
    "vue": "vue-reviewer",
    "flutter": "flutter-reviewer",
    "django": "django-reviewer",
    "fastapi": "fastapi-reviewer",
}


def _instalar(actualizar: bool = False) -> dict[str, Any]:
    from ai_architect import biblioteca

    if biblioteca.instalada() and not actualizar:
        c = biblioteca.cuenta()

        return {
            "respuesta": (
                f"Ya tengo la biblioteca: {c['habilidades']} habilidades, {c['especialistas']} "
                f"especialistas, {c['reglas']} reglas y {c['recetas']} recetas. Di «actualiza la "
                "biblioteca» si quieres la última versión."
            )
        }

    salida = biblioteca.instalar()

    if not salida.get("ok"):
        return {"respuesta": str(salida.get("error"))}

    c = biblioteca.cuenta()

    return {
        "respuesta": (
            f"Biblioteca {'actualizada' if actualizar else 'instalada'}: {c['habilidades']} "
            f"habilidades, {c['especialistas']} especialistas, {c['reglas']} reglas y "
            f"{c['recetas']} recetas."
        )
    }


def _estado() -> dict[str, Any]:
    from ai_architect import biblioteca

    if not biblioteca.instalada():
        return {
            "respuesta": "Todavía no tengo la biblioteca. Di «instala la biblioteca» y la descargo.",
            "mejora": "biblioteca sin instalar",
        }

    e = biblioteca.estado()
    especialistas = [x["nombre"] for x in biblioteca.indice()["especialistas"]]

    return {
        "respuesta": (
            f"Tengo {e['habilidades']} habilidades, {e['especialistas']} especialistas, "
            f"{e['reglas']} reglas y {e['recetas']} recetas. Pregúntame «qué habilidades tienes "
            "para …» o dime «usa la habilidad …»."
        ),
        "panel": {
            "tipo": "texto",
            "titulo": "Biblioteca",
            "cuerpo": "Especialistas: " + ", ".join(especialistas),
        },
    }


def _buscar(tipo: str, tema: str) -> dict[str, Any]:
    from ai_architect import biblioteca

    if not biblioteca.instalada():
        return _estado()

    tipos = {
        "habilidades": "habilidades",
        "skills": "habilidades",
        "especialistas": "especialistas",
        "agentes": "especialistas",
        "reglas": "reglas",
        "recetas": "recetas",
    }
    encontrados = biblioteca.buscar(tema, tipos.get(tipo, ""), 8)

    if not encontrados:
        return {"respuesta": f"No tengo nada para «{tema}» en la biblioteca."}

    nombres = ", ".join(e["nombre"] for e in encontrados)

    return {
        "respuesta": f"Para {tema} tengo {len(encontrados)}: {nombres}.",
        "panel": {
            "tipo": "texto",
            "titulo": f"Biblioteca: {tema}",
            "cuerpo": "\n".join(
                f"• {e['nombre']} [{e['tipo']}]: {e.get('descripcion', '')[:140]}"
                for e in encontrados
            ),
        },
    }


def _especialista_para(nombre: str) -> str:
    """«de seguridad» → security-reviewer; un nombre exacto se respeta."""
    from ai_architect import biblioteca

    limpio = sin_adornos(nombre)
    exacto = biblioteca.especialista(limpio)

    if exacto is not None:
        return str(exacto["nombre"])

    for tema, especialista in TEMAS_A_ESPECIALISTA.items():
        if tema in limpio:
            return especialista

    encontrados = biblioteca.buscar(limpio, "especialistas", 1)

    return encontrados[0]["nombre"] if encontrados else ""


def por_voz(frase: str) -> dict[str, Any] | None:
    limpia = sin_adornos(frase)

    if not limpia:
        return None

    if limpia in INSTALAR or any(limpia.startswith(i) for i in INSTALAR):
        return _instalar()

    if limpia in ACTUALIZAR or any(limpia.startswith(a) for a in ACTUALIZAR):
        return _instalar(actualizar=True)

    m = BUSCAR.match(limpia)

    if m:
        return _buscar(m.group("tipo"), m.group("tema"))

    if limpia in CUANTAS or any(limpia.startswith(c) for c in CUANTAS):
        return _estado()

    original = frase.strip().rstrip(".!?¿¡ ")
    m = USAR.match(original) or USAR.match(limpia)

    if m:
        from ai_architect import biblioteca

        h = biblioteca.habilidad(m.group("nombre"))

        if h is None:
            return {
                "respuesta": f"No tengo la habilidad «{m.group('nombre')}». Pregúntame qué habilidades tengo para ese tema."
            }

        tarea = (
            m.group("tarea").strip() or "aplícala al repositorio y cuéntame qué hiciste"
        )

        return {
            "respuesta": f"Voy con la habilidad {h['nombre']}.",
            "hacer": f"Carga la habilidad «{h['nombre']}» con usar_habilidad y síguela para: {tarea}",
        }

    m = DELEGAR.match(original) or DELEGAR.match(limpia)

    if m:
        from ai_architect import biblioteca

        if not biblioteca.instalada():
            return _estado()

        nombre = _especialista_para(m.group("nombre"))

        if not nombre:
            return {"respuesta": f"No tengo un especialista de {m.group('nombre')}."}

        tarea = m.group("tarea").strip()

        return {
            "respuesta": f"Le paso la tarea a {nombre}.",
            "hacer": (
                f'Delega con la herramienta especialista(nombre="{nombre}", tarea="{tarea}") '
                "y resume su informe en tres frases con lo más importante primero."
            ),
        }

    return None
