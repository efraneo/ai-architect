"""Skills de Architect: recetas en carpeta que el agente ejecuta como herramientas.

Portado de OpenJarvis (Apache-2.0), formato agentskills.io: cada skill es una carpeta con
``SKILL.md`` (frontmatter name/description) o ``skill.toml`` con ``[[skill.steps]]``.

Se buscan en este orden (la primera con ese nombre gana):

1. ``<repositorio>/.architect/skills``  — las del proyecto
2. ``~/.ai_architect/skills``           — las tuyas, para todos los proyectos
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.agente.eventos import EventBus
from ai_architect.agente.herramientas_base import BaseTool
from ai_architect.agente.rutas_agente import get_skills_dir

__all__ = ["carpetas_para", "gestor_para", "herramientas_skills"]

CARPETA_PROYECTO = Path(".architect") / "skills"


def carpetas_para(repositorio: Path | None = None) -> list[Path]:
    carpetas: list[Path] = []
    if repositorio is not None:
        carpetas.append(Path(repositorio).resolve() / CARPETA_PROYECTO)
    carpetas.append(get_skills_dir())
    return carpetas


def gestor_para(repositorio: Path | None = None, bus: EventBus | None = None) -> Any:
    """Un ``SkillManager`` con las skills del proyecto y las globales ya descubiertas."""
    from ai_architect.agente.skills.manager import SkillManager

    gestor = SkillManager(bus or EventBus())
    existentes = [c for c in carpetas_para(repositorio) if c.is_dir()]
    if existentes:
        gestor.discover(existentes)
    return gestor


def herramientas_skills(
    repositorio: Path | None = None,
    ejecutor: Any = None,
    bus: EventBus | None = None,
) -> list[BaseTool]:
    """Las skills como herramientas (``skill_<nombre>``) para la caja del agente."""
    gestor = gestor_para(repositorio, bus)
    if not gestor.skill_names():
        return []
    return list(gestor.get_skill_tools(tool_executor=ejecutor))
