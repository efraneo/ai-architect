"""Los agentes con herramientas de verdad, los tres nuevos, y el equipo como
herramientas de Architect. Sin correr ruff/mypy/git de verdad: se doblan."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.agente import caja
from ai_architect.agente.herramientas import equipo
from ai_architect.agents import (
    calidad_agent,
    empaquetado_agent,
    herramientas_externas,
    voz_agent,
)
from ai_architect.agents.agent_manager import AgentManager


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "1.2.3"\n', encoding="utf-8"
    )
    (tmp_path / "ai_architect").mkdir()
    (tmp_path / "ai_architect" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "ai_architect" / "cosa.py").write_text(
        "\n".join(f"x{i} = {i}" for i in range(20)) + "\n", encoding="utf-8"
    )
    (tmp_path / "ai_architect" / "cli.py").write_text(
        'Comando("analyze", ...)\nComando("hacer", ...)\n', encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("Usa analyze.\n", encoding="utf-8")
    return tmp_path


# --- Calidad --------------------------------------------------------------------------


def test_calidad_corre_black_ruff_y_mypy(repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(calidad_agent, "modulo_disponible", lambda raiz, m: True)

    def correr_falso(orden, cwd, timeout=120):
        if "black" in orden:
            return 1, "would reformat ai_architect/cosa.py\n", ""
        if "ruff" in orden:
            return (
                1,
                '[{"code": "F401", "filename": "ai_architect/cosa.py", "location": {"row": 3}, "message": "import sin usar"}]',
                "",
            )
        if "mypy" in orden:
            return 1, "ai_architect/cosa.py:5: error: Incompatible types\n", ""
        return 0, "", ""

    monkeypatch.setattr(calidad_agent, "correr", correr_falso)

    informe = calidad_agent.CalidadAgent().review(str(repo))

    assert informe["black"] == {"ok": False, "archivos": 1}
    assert informe["ruff"] == {"ok": False, "avisos": 1}
    assert informe["mypy"] == {"ok": False, "errores": 1}
    tipos = [h["type"] for h in informe["findings"]]
    assert "formato" in tipos and "ruff F401" in tipos and "tipos" in tipos
    assert "docstring" in tipos  # cosa.py no tiene docstring
    assert informe["comandos_sin_readme"] == ["hacer"]


def test_calidad_sin_herramientas_no_revienta(repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(calidad_agent, "modulo_disponible", lambda raiz, m: False)

    informe = calidad_agent.CalidadAgent().review(str(repo))

    assert "black" not in informe and informe["status"] == "OK"


# --- Empaquetado ----------------------------------------------------------------------


def test_empaquetado_detecta_version_distinta_y_sin_etiqueta(
    repo: Path, monkeypatch
) -> None:
    (repo / "instalador.iss").write_text(
        '#define Version    "1.0.0"\n', encoding="utf-8"
    )
    (repo / "arquitecto.spec").write_text("Analysis([...])\n", encoding="utf-8")
    monkeypatch.setattr(empaquetado_agent, "hay", lambda p: True)
    monkeypatch.setattr(
        empaquetado_agent, "correr", lambda orden, cwd, timeout=120: (0, "", "")
    )

    informe = empaquetado_agent.EmpaquetadoAgent().review(str(repo))

    tipos = {h["type"] for h in informe["findings"]}
    assert {"version", "spec", "etiqueta"} <= tipos
    assert (
        informe["version_pyproject"] == "1.2.3"
        and informe["version_instalador"] == "1.0.0"
    )


def test_empaquetado_avisa_si_el_instalador_es_viejo(repo: Path, monkeypatch) -> None:
    import os
    import time

    salida = repo / "salida"
    salida.mkdir()
    exe = salida / "ArquitectoSetup.exe"
    exe.write_bytes(b"x")
    viejo = time.time() - 3600
    os.utime(exe, (viejo, viejo))
    monkeypatch.setattr(empaquetado_agent, "hay", lambda p: True)
    monkeypatch.setattr(
        empaquetado_agent,
        "correr",
        lambda orden, cwd, timeout=120: (
            0,
            f"{int(time.time())}\n" if "log" in orden else "v1.2.3\n",
            "",
        ),
    )

    informe = empaquetado_agent.EmpaquetadoAgent().review(str(repo))

    assert any(h["type"] == "instalador" for h in informe["findings"])


# --- Voz y canales ----------------------------------------------------------------------


def test_voz_dice_que_falta(monkeypatch) -> None:
    from ai_architect.voz import escuchar, hablar

    monkeypatch.setattr(
        hablar,
        "motores",
        lambda: {
            "piper": {"disponible": False},
            "openai": {"disponible": False},
            "windows": {"disponible": False},
        },
    )
    monkeypatch.setattr(escuchar, "disponible", lambda: False)

    informe = voz_agent.VozAgent().review(".")

    tipos = {h["type"] for h in informe["findings"]}
    assert "voz" in tipos and "oido" in tipos
    assert "canal telegram" in tipos  # sin claves en las pruebas
    assert informe["canales"]["telegram"] is False


# --- Los existentes, con herramientas ---------------------------------------------------


def test_bug_hunter_suma_ruff(repo: Path, monkeypatch) -> None:
    from ai_architect.agents import bug_hunter_agent

    monkeypatch.setattr(bug_hunter_agent, "modulo_disponible", lambda raiz, m: True)
    monkeypatch.setattr(
        bug_hunter_agent,
        "correr_json",
        lambda orden, cwd, timeout=120: [
            {
                "code": "F821",
                "filename": "ai_architect/cosa.py",
                "location": {"row": 2},
                "message": "nombre sin definir",
            }
        ],
    )

    informe = bug_hunter_agent.BugHunterAgent().review(str(repo))

    assert informe["ruff"] == {"disponible": True, "avisos": 1}
    assert any(h["type"] == "ruff F821" for h in informe["findings"])


def test_git_cuenta_lo_que_no_esta_subido(monkeypatch) -> None:
    from ai_architect.agents import git_agent

    agente = git_agent.GitAgent()
    monkeypatch.setattr(agente, "_ahead", lambda p: 2)
    monkeypatch.setattr(agente, "_behind", lambda p: 0)
    monkeypatch.setattr(
        agente, "_git", lambda p, *a: "abc123 arreglo\n" if "log" in a else ""
    )

    informe = agente.review(".")

    assert informe["commits_hoy"] == ["abc123 arreglo"]
    assert any(
        h["type"] == "sin_subir" and "2 commit" in h["issue"]
        for h in informe.get("findings", [])
    )


def test_release_ve_el_changelog_atrasado(repo: Path) -> None:
    from ai_architect.agents import release_agent

    (repo / "CHANGELOG.md").write_text("## 1.0.0\n- algo\n", encoding="utf-8")

    informe = release_agent.ReleaseAgent().review(str(repo))

    assert informe["version_declarada"] == "1.2.3"
    assert any(h["type"] == "changelog_atrasado" for h in informe["findings"])


def test_devops_avisa_si_la_ci_fallo(repo: Path, monkeypatch) -> None:
    from ai_architect.agents import devops_agent

    monkeypatch.setattr(devops_agent, "hay", lambda p: True)
    monkeypatch.setattr(
        devops_agent,
        "correr_json",
        lambda orden, cwd, timeout=120: [
            {"conclusion": "failure", "displayTitle": "Rompí algo"}
        ],
    )

    informe = devops_agent.DevOpsAgent().review(str(repo))

    assert informe["ci_github"]["conclusion"] == "failure"
    assert any(h["type"] == "ci" for h in informe["findings"])


def test_testing_cuenta_con_pytest(repo: Path, monkeypatch) -> None:
    from ai_architect.agents import testing_agent

    monkeypatch.setattr(testing_agent, "modulo_disponible", lambda raiz, m: True)
    monkeypatch.setattr(
        testing_agent,
        "correr",
        lambda orden, cwd, timeout=120: (0, "1435 tests collected in 3.2s\n", ""),
    )

    informe = testing_agent.TestingAgent().review(str(repo))

    assert informe["pruebas_recogidas"] == 1435


# --- El equipo, orquestado por Architect ---------------------------------------------------


def test_los_tres_agentes_nuevos_estan_en_el_equipo() -> None:
    gestor = AgentManager()

    assert gestor.calidad.name.startswith("Calidad")
    assert gestor.voz.name.startswith("Voz")
    assert gestor.empaquetado.name.startswith("Empaquetado")


def test_el_equipo_entra_en_la_caja_como_herramientas(tmp_path: Path) -> None:
    nombres = caja.nombres(caja.herramientas_para(tmp_path))

    assert "equipo" in nombres
    for clave in equipo.EQUIPO:
        assert f"agente_{clave}" in nombres, clave

    for h in caja.herramientas_para(tmp_path):
        if h.spec.name.startswith("agente_") or h.spec.name == "equipo":
            assert h.spec.requires_confirmation is False


def test_la_herramienta_de_un_agente_devuelve_sus_hallazgos(tmp_path: Path) -> None:
    herramienta = equipo.AgenteTool("publicacion", str(tmp_path))

    informe = {
        "findings": [{"type": "sin_changelog", "issue": "no hay CHANGELOG"}],
        "release_ready": False,
        "status": "OK",
    }

    with mock.patch(
        "ai_architect.agents.release_agent.ReleaseAgent.review", return_value=informe
    ):
        resultado = herramienta.execute()

    assert (
        resultado.success
        and "sin_changelog" in resultado.content
        and "release_ready" in resultado.content
    )


def test_el_guion_le_dice_a_architect_que_reparta(tmp_path: Path) -> None:
    from ai_architect.agente.guion import prompt_sistema

    texto = prompt_sistema(tmp_path, "Efraín", False)

    assert "EQUIPO" in texto and "agente_calidad" in texto and "orquesta" in texto


def test_las_skills_del_proyecto_se_descubren() -> None:
    from ai_architect.agente import skills

    raiz = Path(__file__).resolve().parents[2]
    gestor = skills.gestor_para(raiz)

    assert {"revision-completa", "salud", "listo-para-publicar"} <= set(
        gestor.skill_names()
    )


def test_las_herramientas_externas_no_revientan_sin_programa(tmp_path: Path) -> None:
    codigo, _, err = herramientas_externas.correr(
        ["programa-que-no-existe-xyz"], tmp_path, 5
    )

    assert codigo == -1 and err
    assert (
        herramientas_externas.correr_json(["programa-que-no-existe-xyz"], tmp_path, 5)
        is None
    )
