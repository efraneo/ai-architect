"""Preguntar lo que falta, en vez de adivinarlo.

Dos mitades, y las dos importan igual:

- Que **pregunte** cuando no sabe sobre qué repositorio trabajar.
- Que **no pregunte** cuando ya se lo han dicho. Confirmar cada orden es
  un paso de más en cada frase, y eso cansa a la tercera.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect.commands import encargo


@pytest.fixture(autouse=True)
def sin_encargos():
    encargo.olvidar()

    yield

    encargo.olvidar()


# --- Cuándo falta el sitio --------------------------------------------------


@pytest.mark.parametrize(
    "frase",
    [
        "evaluemos un repositorio",
        "analicemos un proyecto",
        "revisemos el código",
        "vamos a revisar un repositorio",
        "quiero analizar un programa",
    ],
)
def test_pregunta_cuando_no_dice_cual(frase: str) -> None:
    assert encargo.falta_el_sitio(frase, "analyze", "") is True


@pytest.mark.parametrize(
    ("frase", "carpeta"),
    [
        ("analiza la carpeta autosgsst", "autosgsst"),
        ("revisa autosgsst", "autosgsst"),
    ],
)
def test_no_pregunta_si_ya_lo_dijo(frase: str, carpeta: str) -> None:
    """Confirmar lo que ya se dijo es un paso de más en cada orden."""
    assert encargo.falta_el_sitio(frase, "analyze", carpeta) is False


def test_tampoco_pregunta_por_una_orden_normal() -> None:
    """ "Revisa" estando dentro de un repositorio habla de ese."""
    assert encargo.falta_el_sitio("revisa", "review", "") is False


def test_lo_que_no_trabaja_sobre_un_repositorio_no_pregunta() -> None:
    assert encargo.falta_el_sitio("evaluemos un repositorio", "doctor", "") is False


# --- El ida y vuelta --------------------------------------------------------


def test_anota_y_dice_lo_que_entendio() -> None:
    salida = encargo.anotar("review", "evaluemos un repositorio", {"comando": "review"})

    assert salida["awaiting"] == "sitio"
    assert "puntuarlo" in salida["explanation"]
    assert "Dónde está" in salida["explanation"]
    assert encargo.hay_encargo() is True


def test_con_el_sitio_devuelve_el_encargo_listo(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "autosgsst").mkdir()
    monkeypatch.setenv("AI_ARCHITECT_RAICES", str(tmp_path))

    encargo.anotar("analyze", "analicemos un repositorio", {"comando": "analyze"})

    vuelta = encargo.con_el_sitio("autosgsst", tmp_path)

    assert vuelta is not None
    assert vuelta["listo"] is True
    assert vuelta["comando"] == "analyze"
    assert vuelta["sitio"].name == "autosgsst"
    assert encargo.hay_encargo() is False


def test_la_carpeta_dicha_manda_sobre_la_del_modelo(
    tmp_path: Path, monkeypatch
) -> None:
    """El fallo que este módulo venía a evitar, y que cometió igual.

    Se resolvía "autosgsst" bien y se analizaba AI-architect: el modelo
    había puesto `project: "."` y ese punto ganaba, porque `_argumentos`
    mira primero lo que trae la intención.
    """
    (tmp_path / "autosgsst").mkdir()
    monkeypatch.setenv("AI_ARCHITECT_RAICES", str(tmp_path))

    encargo.anotar("analyze", "x", {"comando": "analyze", "project": "."})

    vuelta = encargo.con_el_sitio("autosgsst", tmp_path)

    assert vuelta is not None
    assert vuelta["intencion"]["project"].endswith("autosgsst")


def test_se_entiende_dicho_con_rodeos(tmp_path: Path, monkeypatch) -> None:
    """Nadie contesta el nombre a secas: dice "está en la carpeta tal"."""
    (tmp_path / "autosgsst").mkdir()
    monkeypatch.setenv("AI_ARCHITECT_RAICES", str(tmp_path))

    encargo.anotar("analyze", "x", {})

    vuelta = encargo.con_el_sitio("está en la carpeta autosgsst", tmp_path)

    assert vuelta is not None and vuelta["listo"] is True


def test_si_no_encuentra_la_carpeta_ofrece_las_parecidas(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "informes").mkdir()
    (tmp_path / "informes2").mkdir()
    monkeypatch.setenv("AI_ARCHITECT_RAICES", str(tmp_path))

    encargo.anotar("analyze", "x", {})

    vuelta = encargo.con_el_sitio("informe", tmp_path)

    assert vuelta is not None
    assert vuelta["awaiting"] == "sitio"
    assert "informes" in vuelta["explanation"]
    assert encargo.hay_encargo() is True, "sigue esperando, no se pierde el encargo"


def test_se_puede_desistir() -> None:
    encargo.anotar("analyze", "x", {})

    vuelta = encargo.con_el_sitio("déjalo", ".")

    assert vuelta is not None and vuelta["cancelado"] is True
    assert encargo.hay_encargo() is False


def test_si_no_parece_una_ubicacion_sigue_su_camino(
    tmp_path: Path, monkeypatch
) -> None:
    """Puede haber cambiado de tema: eso no es la respuesta a la pregunta."""
    monkeypatch.setenv("AI_ARCHITECT_RAICES", str(tmp_path))

    encargo.anotar("analyze", "x", {})

    assert encargo.con_el_sitio("mejor cuéntame un chiste", tmp_path) is None


def test_sin_encargo_pendiente_no_interpreta_nada() -> None:
    assert encargo.con_el_sitio("autosgsst", ".") is None
