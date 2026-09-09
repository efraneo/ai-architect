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

    # Ningún canal real: ni el Telegram ni el correo del usuario se tocan en
    # una prueba, tenga lo que tenga en su .env.
    from ai_architect import canales

    monkeypatch.setattr(canales, "_cargar", lambda: None)

    import os

    # Todas las de canales, incluidas las que otra prueba haya podido dejar en el
    # entorno al «configurar hablando» (guardar_en_env escribe en os.environ).
    for variable in list(os.environ):
        if variable.startswith(("TELEGRAM_", "CORREO_", "WHATSAPP_")):
            monkeypatch.delenv(variable, raising=False)


@pytest.fixture(autouse=True)
def _sin_ventanas_ni_programas(monkeypatch: pytest.MonkeyPatch):
    """Una prueba nunca abre el navegador, Chrome en modo aplicación, un
    programa del PC ni Word: en la máquina de Efraín la batería dejó abiertas
    varias ventanas de Chrome con el aviso de «línea de comandos no admitida».
    Las pruebas que quieran comprobar esas llamadas las doblan ellas mismas."""
    import webbrowser

    from ai_architect.commands import abrir, avatar
    from ai_architect.office import word

    monkeypatch.setattr(webbrowser, "open", lambda *a, **k: True)
    monkeypatch.setattr(avatar, "abrir_en_navegador", lambda url: "prueba")
    monkeypatch.setattr(avatar, "ventana_flotante", lambda *a, **k: True)
    monkeypatch.setattr(abrir, "_lanzar", lambda objetivo: None)
    monkeypatch.setattr(
        word, "_app", lambda: (_ for _ in ()).throw(RuntimeError("sin Word en pruebas"))
    )
