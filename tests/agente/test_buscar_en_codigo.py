"""Buscar en el código sin rg ni grep, y una consola que dice cuando falta el programa."""

from __future__ import annotations

from pathlib import Path

from ai_architect.agente import caja
from ai_architect.agente.herramientas.buscar import BuscarEnCodigoTool, buscar


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "web.py").write_text(
        "import subprocess\n\ndef correr(orden):\n    return subprocess.run(orden, shell=True)\n",
        encoding="utf-8",
    )
    (tmp_path / "app" / "vista.html").write_text(
        "<div id='x'></div>\n<script>el.innerHTML = t;</script>\n", encoding="utf-8"
    )
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "lib.py").write_text("shell=True\n", encoding="utf-8")
    return tmp_path


def test_busca_por_regex_sin_mayusculas_y_sin_el_venv(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    lineas = buscar(repo, r"SHELL\s*=\s*true")

    assert lineas == ["app/web.py:4: return subprocess.run(orden, shell=True)"]


def test_acota_por_ruta_extension_y_contexto(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    assert buscar(repo, "innerHTML", extension="py") == []
    assert buscar(repo, "innerHTML", ruta="app", extension="html")[0].startswith(
        "app/vista.html:2"
    )
    con_contexto = buscar(repo, "def correr", contexto=1)
    assert con_contexto[0].endswith("-") or "web.py:2-" in con_contexto[0]
    assert any("web.py:3:" in ln for ln in con_contexto) and con_contexto[-1] == "--"
    assert buscar(repo, "x", ruta="../..") == []


def test_un_patron_roto_se_busca_literal(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    assert buscar(repo, "run(orden") and buscar(repo, "[") == []


def test_la_herramienta_esta_en_la_caja_y_no_pide_permiso(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    herramientas = {h.spec.name: h for h in caja.herramientas_para(repo)}

    assert "buscar_en_codigo" in herramientas
    assert herramientas["buscar_en_codigo"].spec.requires_confirmation is False
    assert "buscar_en_codigo" not in caja.ESCRIBEN

    r = herramientas["buscar_en_codigo"].execute(patron="shell=True")
    assert r.success and "app/web.py:4" in r.content

    r = herramientas["buscar_en_codigo"].execute(patron="nada-de-nada")
    assert r.success and "Nada casa" in r.content

    assert BuscarEnCodigoTool(str(repo)).execute(patron="").success is False


def test_la_consola_dice_que_falta_el_programa(tmp_path: Path) -> None:
    herramientas = {h.spec.name: h for h in caja.herramientas_para(tmp_path)}

    r = herramientas["shell_exec"].execute(command="rg -n innerHTML .")

    assert not r.success
    assert "no está instalado" in r.content and "buscar_en_codigo" in r.content


def test_el_guion_manda_a_buscar_en_codigo(tmp_path: Path) -> None:
    from ai_architect.agente.guion import prompt_sistema

    assert "buscar_en_codigo" in prompt_sistema(tmp_path, "Efraín", False)
