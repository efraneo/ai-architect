"""``ai-architect agents`` exposes the orchestrator from the command line.

The static agents run by default: no API key, no cost. ``--ai`` also runs
the five AI agents, and that is opt-in on purpose -- five provider calls
are not something anyone should trigger by accident.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.cli import build_parser
from ai_architect.commands import agents


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    """A small but complete project: nothing here should raise a finding."""
    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("httpx\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# 1.0\n", encoding="utf-8")

    flujos = tmp_path / ".github" / "workflows"
    flujos.mkdir(parents=True)
    (flujos / "ci.yml").write_text("on: push\n", encoding="utf-8")

    return tmp_path


# --- El comando existe ------------------------------------------------------


def test_el_parser_acepta_agents() -> None:
    assert build_parser().parse_args(["agents", "."]).command == "agents"


def test_hay_una_bandera_para_la_ia() -> None:
    assert build_parser().parse_args(["agents", ".", "--ai"]).ai is True


def test_la_ia_esta_apagada_por_defecto() -> None:
    """Money is not spent unless it is asked for."""
    assert build_parser().parse_args(["agents", "."]).ai is False


# --- Lo que devuelve --------------------------------------------------------


def test_inspecciona_el_proyecto(proyecto: Path) -> None:
    resultado = agents.run(str(proyecto))

    assert resultado["success"] is True
    assert resultado["repository"] == str(proyecto.resolve())


def test_reporta_los_once_agentes_estaticos(proyecto: Path) -> None:
    assert agents.run(str(proyecto))["agents"] == [
        "architecture",
        "bugs",
        "dependencies",
        "devops",
        "git",
        "licenses",
        "metrics",
        "performance",
        "release",
        "security",
        "testing",
    ]


def test_un_proyecto_limpio_no_tiene_hallazgos(proyecto: Path) -> None:
    resultado = agents.run(str(proyecto))

    assert resultado["total_findings"] == 0
    assert resultado["findings"] == []


def test_un_secreto_se_reporta(proyecto: Path) -> None:
    (proyecto / "config.py").write_text('password = "x"\n', encoding="utf-8")

    resultado = agents.run(str(proyecto))

    assert resultado["total_findings"] == 1


def test_sin_ia_no_se_llama_al_proveedor(proyecto: Path) -> None:
    with mock.patch(
        "ai_architect.agents.agent_manager.AgentManager.execute"
    ) as ejecutar:
        agents.run(str(proyecto))

    ejecutar.assert_not_called()


def test_con_ia_se_ejecuta_todo(proyecto: Path) -> None:
    contexto = mock.Mock()
    contexto.data = {"metrics": {"status": "OK"}, "architect": {"status": "OK"}}

    with mock.patch(
        "ai_architect.agents.agent_manager.AgentManager.execute",
        return_value=contexto,
    ) as ejecutar:
        resultado = agents.run(str(proyecto), ai=True)

    ejecutar.assert_called_once()
    assert resultado["ai"] is True
    assert "architect" in resultado["agents"]


# --- Los fallos -------------------------------------------------------------


def test_un_repositorio_inexistente_falla_con_claridad(tmp_path: Path) -> None:
    resultado = agents.run(str(tmp_path / "no-existe"))

    assert resultado["success"] is False
    assert resultado["error"] == "Repository not found."


def test_un_fallo_del_gestor_no_revienta_el_comando(proyecto: Path) -> None:
    with mock.patch(
        "ai_architect.agents.agent_manager.AgentManager.inspect",
        side_effect=RuntimeError("se rompió"),
    ):
        resultado = agents.run(str(proyecto))

    assert resultado["success"] is False
    assert resultado["error"] == "se rompió"
