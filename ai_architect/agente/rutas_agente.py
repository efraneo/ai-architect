"""Dónde guarda Architect lo suyo (memoria, skills, MCP, aprobaciones).

OpenJarvis usaba ``~/.openjarvis``; aquí todo vive en la misma carpeta que el perfil y el
``.env`` de AI-architect: ``~/.ai_architect`` (o ``ARCHITECT_HOME`` si se define).
"""

from __future__ import annotations

import os
from pathlib import Path


def get_config_dir() -> Path:
    raiz = os.environ.get("ARCHITECT_HOME")
    carpeta = Path(raiz).expanduser() if raiz else Path.home() / ".ai_architect"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def get_data_dir() -> Path:
    return get_config_dir()


def get_skills_dir() -> Path:
    carpeta = get_config_dir() / "skills"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def get_memory_dir() -> Path:
    return get_config_dir()
