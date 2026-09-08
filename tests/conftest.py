"""Aislamiento común a todas las pruebas.

Lo que Architect guarda por su cuenta —memoria, skills, MCP, cola de
aprobaciones— vive en ``~/.ai_architect`` (``ARCHITECT_HOME``). Sin esto, una
prueba de ``hacer`` sin ``--si`` dejaba sus escrituras negadas **en la cola de
verdad** del usuario: aparecieron seis «escribir …\\pytest-of-…\\modulo.py»
esperando permiso en su máquina. Cada prueba se lleva su carpeta temporal.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _casa_de_architect_aislada(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARCHITECT_HOME", str(tmp_path / ".ai_architect"))
