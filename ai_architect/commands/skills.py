"""
=========================================================
Skills

Recetas reutilizables que Architect puede ejecutar como una herramienta más.
=========================================================

Formato agentskills.io (portado de OpenJarvis, Apache-2.0): una carpeta por skill con un
``SKILL.md`` (frontmatter con name/description) o un ``skill.toml`` con ``[[skill.steps]]``
que encadenan herramientas (``file_read``, ``shell_exec``…) con plantillas ``{placeholder}``.

Dónde se buscan, en este orden (la primera que aparece gana):
1. ``<repositorio>/.architect/skills/``   — skills del proyecto
2. ``~/.ai_architect/skills/``            — skills tuyas, para todos los proyectos

    architect skills [repositorio]      lista las skills disponibles
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.agente import skills as mod_skills


def run(project: str = ".") -> dict[str, Any]:
    repositorio = Path(project).resolve()
    gestor = mod_skills.gestor_para(repositorio)
    nombres = gestor.skill_names()
    filas = []
    for n in nombres:
        m = gestor.resolve(n)
        filas.append(
            {"nombre": n, "descripcion": m.description, "pasos": len(m.steps or [])}
        )
    carpetas = ", ".join(str(c) for c in mod_skills.carpetas_para(repositorio))
    if not filas:
        dicho = f"No hay skills. Crea una carpeta con un skill.toml en {carpetas}."
    else:
        dicho = f"{len(filas)} skill(s): " + ", ".join(f["nombre"] for f in filas) + "."
    return {
        "success": True,
        "executed": False,
        "command": "skills",
        "instant": True,
        "skills": filas,
        "folders": carpetas,
        "explanation": dicho,
        "panel": {
            "tipo": "texto",
            "titulo": "Skills",
            "cuerpo": "\n".join(
                f"{f['nombre']} · {f['pasos']} paso(s) · {f['descripcion']}"
                for f in filas
            )
            or dicho,
        },
    }
