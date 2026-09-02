"""De un nombre dicho en voz alta a una carpeta de verdad.

Hablando no se dictan rutas: se dice "revisa autosgsst". Lo que se fija
aquí es sobre todo cuándo **no** hay que elegir — ejecutar comandos sobre
la carpeta equivocada es peor que perder un segundo preguntando.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect.core import rutas


@pytest.fixture
def arbol(tmp_path: Path, monkeypatch):
    """Un par de carpetas donde buscar, sin tocar el disco de verdad."""
    for nombre in ("autosgsst", "AI-architect", "notas", ".git", "node_modules"):
        (tmp_path / nombre).mkdir()

    (tmp_path / "AI-architect" / "ai_architect").mkdir()

    monkeypatch.setenv("AI_ARCHITECT_RAICES", str(tmp_path))

    return tmp_path


def test_encuentra_la_carpeta_por_su_nombre(arbol: Path) -> None:
    elegida, _ = rutas.resolver("autosgsst", arbol)

    assert elegida is not None
    assert elegida.name == "autosgsst"


def test_no_le_importan_las_mayusculas_ni_las_tildes(arbol: Path) -> None:
    """Whisper escribe como quiere; el disco no."""
    elegida, _ = rutas.resolver("AutoSGSST", arbol)

    assert elegida is not None and elegida.name == "autosgsst"


def test_baja_un_nivel(arbol: Path) -> None:
    elegida, _ = rutas.resolver("ai_architect", arbol)

    assert elegida is not None
    assert elegida.name == "ai_architect"


def test_una_ruta_de_verdad_no_se_adivina(arbol: Path) -> None:
    elegida, _ = rutas.resolver(str(arbol / "notas"), arbol)

    assert elegida == (arbol / "notas").resolve()


def test_lo_que_no_esta_no_se_inventa(arbol: Path) -> None:
    elegida, _ = rutas.resolver("contabilidad", arbol)

    assert elegida is None


def test_ante_la_duda_se_ofrecen_las_parecidas(tmp_path: Path, monkeypatch) -> None:
    """Elegir a ciegas entre dos que suenan igual es lo que no hay que hacer."""
    (tmp_path / "informes").mkdir()
    (tmp_path / "informes2").mkdir()

    monkeypatch.setenv("AI_ARCHITECT_RAICES", str(tmp_path))

    elegida, parecidas = rutas.resolver("informe", tmp_path)

    assert elegida is None
    assert len(parecidas) >= 2


def test_no_se_mete_en_venv_ni_en_git(arbol: Path) -> None:
    """Un recorrido sin filtro devuelve cientos de carpetas de ruido."""
    nombres = {c.name for c in rutas.carpetas(arbol)}

    assert ".git" not in nombres
    assert "node_modules" not in nombres


def test_un_nombre_vacio_no_devuelve_nada(arbol: Path) -> None:
    assert rutas.resolver("  ", arbol) == (None, [])


def test_se_nombran_como_se_dicen(arbol: Path) -> None:
    dicho = rutas.nombrar([arbol / "autosgsst", arbol / "notas"])

    assert dicho == "autosgsst, notas"
