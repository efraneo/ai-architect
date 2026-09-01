"""``agents/`` was orphaned: nobody built an ``AgentManager``.

``execute()`` runs the eleven static agents **and** the five AI ones, which
means five provider calls -- too expensive to hang off every improvement.
``inspect()`` is the free half, and ``findings_de()`` turns it into the
findings list the decision engine reads.

No test here touches an LLM: only the static half is exercised.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.agents.agent_manager import AgentManager


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    """A small but complete project: nothing here should raise a finding."""
    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")
    (tmp_path / "test_modulo.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("httpx\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# 1.0\n", encoding="utf-8")

    flujos = tmp_path / ".github" / "workflows"
    flujos.mkdir(parents=True)
    (flujos / "ci.yml").write_text("on: push\n", encoding="utf-8")

    return tmp_path


@pytest.fixture
def manager() -> AgentManager:
    return AgentManager()


# --- La inspección gratuita -------------------------------------------------


def test_estan_los_once_agentes_estaticos(
    manager: AgentManager, proyecto: Path
) -> None:
    inspeccion = manager.inspect(str(proyecto))

    assert set(inspeccion) == {
        "metrics",
        "architecture",
        "testing",
        "security",
        "dependencies",
        "licenses",
        "git",
        "bugs",
        "performance",
        "devops",
        "release",
    }


def test_no_se_llama_a_ningun_agente_de_ia(
    manager: AgentManager, proyecto: Path
) -> None:
    """That is the whole point: no provider calls, no cost."""
    for agente in (
        manager.architect,
        manager.refactor,
        manager.reviewer,
        manager.tests,
        manager.documentation,
    ):
        agente.run = mock.Mock()  # type: ignore[method-assign]

    manager.inspect(str(proyecto))

    for agente in (manager.architect, manager.refactor, manager.reviewer):
        agente.run.assert_not_called()


def test_cada_agente_reporta_lo_suyo(manager: AgentManager, proyecto: Path) -> None:
    inspeccion = manager.inspect(str(proyecto))

    assert inspeccion["metrics"]["python_files"] == 2
    assert inspeccion["dependencies"]["dependency_count"] == 1


# --- Un agente que falla no tumba a los demás -------------------------------


def test_si_un_agente_revienta_los_otros_siguen(
    manager: AgentManager, proyecto: Path
) -> None:
    manager.security.review = mock.Mock(  # type: ignore[method-assign]
        side_effect=RuntimeError("se rompió")
    )

    inspeccion = manager.inspect(str(proyecto))

    assert inspeccion["security"]["status"] == "error"
    assert inspeccion["security"]["error"] == "se rompió"
    assert inspeccion["metrics"]["status"] == "OK"


# --- Los hallazgos ----------------------------------------------------------


def test_un_proyecto_limpio_no_genera_hallazgos(
    manager: AgentManager, proyecto: Path
) -> None:
    assert manager.findings_de(manager.inspect(str(proyecto))) == []


def test_un_secreto_de_verdad_si_se_reporta(
    manager: AgentManager, proyecto: Path
) -> None:
    (proyecto / "config.py").write_text(
        'password = "hunter2"\n',
        encoding="utf-8",
    )

    hallazgos = manager.findings_de(manager.inspect(str(proyecto)))

    assert any("Password Assignment" in h for h in hallazgos)


def test_el_hallazgo_dice_de_que_agente_viene(
    manager: AgentManager, proyecto: Path
) -> None:
    (proyecto / "config.py").write_text('password = "x"\n', encoding="utf-8")

    hallazgos = manager.findings_de(manager.inspect(str(proyecto)))

    assert all(h.startswith("security:") for h in hallazgos)


def test_el_hallazgo_dice_en_que_archivo_esta(
    manager: AgentManager, proyecto: Path
) -> None:
    """ "security: Password Assignment" a secas no sirve para nada."""
    (proyecto / "config.py").write_text('password = "x"\n', encoding="utf-8")

    hallazgos = manager.findings_de(manager.inspect(str(proyecto)))

    assert any("config.py" in h for h in hallazgos)


def test_cuando_hay_linea_tambien_se_dice(
    manager: AgentManager, proyecto: Path
) -> None:
    """A bug hunter that does not say where is not much of a hunter."""
    (proyecto / "roto.py").write_text(
        "try:\n    pass\nexcept Exception:\n    pass\n",
        encoding="utf-8",
    )

    hallazgos = manager.findings_de(manager.inspect(str(proyecto)))

    assert any("roto.py:3" in h for h in hallazgos)


def test_un_agente_en_error_es_un_hallazgo(manager: AgentManager) -> None:
    hallazgos = manager.findings_de({"git": {"status": "error", "error": "x"}})

    assert hallazgos == ["git: no se pudo revisar"]


def test_los_hallazgos_en_texto_plano_tambien_valen(manager: AgentManager) -> None:
    """Not every agent reports dicts."""
    hallazgos = manager.findings_de({"testing": {"findings": ["sin pruebas"]}})

    assert hallazgos == ["testing: sin pruebas"]


def test_lo_que_no_es_un_diccionario_se_ignora(manager: AgentManager) -> None:
    assert manager.findings_de({"raro": "una cadena suelta"}) == []


def test_una_inspeccion_vacia_no_genera_hallazgos(manager: AgentManager) -> None:
    assert manager.findings_de({}) == []


# --- Lo que ya no reporta ---------------------------------------------------


def test_no_reporta_los_secretos_de_las_dependencias(
    manager: AgentManager, proyecto: Path
) -> None:
    """The regression: fifteen findings, all of them inside ``.venv``."""
    paquete = proyecto / ".venv" / "Lib" / "site-packages" / "httpx"
    paquete.mkdir(parents=True)
    (paquete / "_urls.py").write_text('password = "x"\n', encoding="utf-8")

    assert manager.findings_de(manager.inspect(str(proyecto))) == []


def test_las_metricas_no_cuentan_el_venv(manager: AgentManager, proyecto: Path) -> None:
    paquete = proyecto / ".venv" / "Lib"
    paquete.mkdir(parents=True)
    (paquete / "otro.py").write_text("x = 1\n", encoding="utf-8")

    assert manager.inspect(str(proyecto))["metrics"]["python_files"] == 2


def test_el_escaner_no_se_delata_a_si_mismo(
    manager: AgentManager, proyecto: Path
) -> None:
    """Its own pattern table matches its own patterns."""
    inspeccion = manager.inspect(str(Path("ai_architect/agents").resolve()))

    hallazgos = manager.findings_de(inspeccion)

    assert [h for h in hallazgos if h.startswith("security:")] == []
