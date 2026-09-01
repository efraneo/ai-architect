"""``architect doctor``: el comando que antes no podía dar mal.

Devolvía ``"status": "healthy"`` fijo, junto a la versión de Python y la
plataforma. Sin una sola clave de proveedor configurada y sin git instalado,
seguía diciendo que todo iba bien. Es lo primero que el README manda
ejecutar, así que era justo el sitio donde menos convenía mentir.

La prueba que había —``assert result["status"] == "healthy"``— pasaba por
eso mismo: no comprobaba el diagnóstico, comprobaba una constante.

Ninguna prueba de aquí llama a un proveedor ni sale a la red.
"""

from __future__ import annotations

import json
import os
from unittest import mock

import pytest

from ai_architect.commands import doctor


@pytest.fixture
def sin_claves():
    limpio = {
        k: v
        for k, v in os.environ.items()
        if not k.endswith("_API_KEY") and k != "DEFAULT_PROVIDER"
    }

    with mock.patch.dict(os.environ, limpio, clear=True):
        yield


# --- Lo que siempre informa -------------------------------------------------


def test_informa_python_y_plataforma() -> None:
    informe = doctor.run()

    assert informe["success"] is True
    assert informe["python"]
    assert informe["platform"]


def test_informa_de_cada_componente() -> None:
    componentes = doctor.run()["components"]

    assert "provider" in componentes
    assert "agents" in componentes
    assert "git" in componentes


# --- Ahora sí puede dar mal -------------------------------------------------


def test_sin_clave_de_proveedor_no_esta_sano(sin_claves) -> None:
    """La regresión: esto respondía "healthy" igualmente."""
    informe = doctor.run()

    assert informe["healthy"] is False
    assert informe["status"] == "degraded"
    assert informe["components"]["provider"]["status"] == "not_configured"


def test_con_clave_el_proveedor_esta_listo() -> None:
    entorno = {"OPENAI_API_KEY": "sk-de-prueba", "DEFAULT_PROVIDER": "openai"}

    with mock.patch.dict(os.environ, entorno):
        informe = doctor.run()

    assert informe["components"]["provider"]["status"] == "ready"


def test_sin_git_no_esta_sano() -> None:
    with mock.patch("shutil.which", return_value=None):
        informe = doctor.run()

    assert informe["healthy"] is False
    assert informe["components"]["git"]["status"] == "unavailable"
    assert "PATH" in informe["components"]["git"]["detail"]


def test_con_git_lo_dice() -> None:
    informe = doctor.run()

    assert informe["components"]["git"]["status"] == "OK"


# --- El diagnóstico no puede reventar ---------------------------------------


def test_si_el_proveedor_no_se_puede_construir_se_anota() -> None:
    """Un diagnóstico que lanza no diagnostica: informa de que falla."""
    with mock.patch(
        "ai_architect.providers.provider_manager.ProviderManager",
        side_effect=RuntimeError("sin proveedores"),
    ):
        informe = doctor.run()

    assert informe["components"]["provider"]["status"] == "unavailable"
    assert informe["healthy"] is False


def test_si_los_agentes_no_se_pueden_construir_se_anota() -> None:
    """Doce agentes no se podían instanciar y nadie se enteró, porque nadie
    los construía. Esto lo habría dicho."""
    with mock.patch(
        "ai_architect.agents.agent_manager.AgentManager",
        side_effect=TypeError("Can't instantiate abstract class"),
    ):
        informe = doctor.run()

    assert informe["components"]["agents"]["status"] == "unavailable"
    assert "abstract" in informe["components"]["agents"]["detail"]


def test_si_git_no_se_puede_ejecutar_se_anota() -> None:
    with mock.patch("subprocess.run", side_effect=OSError("no se pudo lanzar")):
        informe = doctor.run()

    assert informe["components"]["git"]["status"] == "unavailable"


def test_el_informe_es_serializable() -> None:
    assert json.dumps(doctor.run(), default=str)
