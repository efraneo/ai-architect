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
    monkeypatch.setenv("ARCHITECT_SIN_INSTALAR", "1")

    for variable in list(os.environ):
        if variable.startswith(("TELEGRAM_", "CORREO_", "WHATSAPP_", "HOGAR_")):
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
    # Sin Chrome ni Edge «encontrados»: abrir_en_navegador cae al webbrowser doblado.
    monkeypatch.setattr(avatar, "_navegador_chromium", lambda: None)
    monkeypatch.setattr(abrir, "_lanzar", lambda objetivo: None)
    monkeypatch.setattr(
        word, "_app", lambda: (_ for _ in ()).throw(RuntimeError("sin Word en pruebas"))
    )
    # Ni el CLI de Claude Code: con él instalado, un «adelante» de prueba lo
    # lanzaba de verdad sobre la carpeta temporal (hasta media hora y con
    # costo). Las pruebas de esa vía quitan la variable y doblan `shutil.which`.
    monkeypatch.setenv("ARCHITECT_REPARADOR", "hacer")


@pytest.fixture(autouse=True)
def _pide_sin_estado_de_otra_prueba():
    """`conversar.run` deja a `pide` en modo conciso y con el saludo dado: cada
    prueba empieza como si nadie hubiera hablado."""
    from ai_architect.commands import pide

    pide.conciso(False)
    pide.reiniciar_saludo()

    yield

    pide.conciso(False)


@pytest.fixture(autouse=True)
def _agentes_sin_herramientas_externas(monkeypatch: pytest.MonkeyPatch):
    """Dentro de la batería ningún agente corre pip, pytest, gh, ruff o mypy de
    verdad: tardan, dependen de la máquina y una prueba que lanza pytest dentro
    de pytest se muerde la cola. Cada módulo de agente ve las herramientas
    externas como ausentes; la prueba que necesite una, la dobla encima."""
    import importlib
    import pkgutil

    from ai_architect import agents

    dobles = {
        "correr": lambda orden, cwd, timeout=120: (-1, "", "no disponible en pruebas"),
        "correr_json": lambda orden, cwd, timeout=120: None,
        "hay": lambda programa: False,
        "modulo_disponible": lambda raiz, modulo: False,
    }

    for info in pkgutil.iter_modules(agents.__path__):
        if info.name == "herramientas_externas":
            continue

        modulo = importlib.import_module(f"ai_architect.agents.{info.name}")

        for nombre, doble in dobles.items():
            if hasattr(modulo, nombre):
                monkeypatch.setattr(modulo, nombre, doble)
