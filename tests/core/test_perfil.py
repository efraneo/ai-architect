"""El perfil: a quién le habla y cómo.

Una herramienta que te trata igual el primer día que el año siguiente no se
siente tuya. Esto guarda lo mínimo para que no lo sea, y **ni una
credencial**: un nombre y un trato.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from ai_architect.core import perfil


@pytest.fixture
def archivo(tmp_path: Path) -> Path:
    return tmp_path / "perfil.json"


# --- El saludo según la hora ------------------------------------------------


@pytest.mark.parametrize(
    ("hora", "esperado"),
    [
        (6, "Buenos días"),
        (11, "Buenos días"),
        (12, "Buenas tardes"),
        (19, "Buenas tardes"),
        (20, "Buenas noches"),
        (3, "Buenas noches"),
    ],
)
def test_saluda_segun_la_hora(hora: int, esperado: str) -> None:
    assert perfil.saludo(datetime(2026, 9, 1, hora)) == esperado


def test_la_madrugada_sigue_siendo_de_noche() -> None:
    """Quien trabaja a las tres de la mañana no está en la mañana."""
    assert perfil.saludo(datetime(2026, 9, 1, 3)) == "Buenas noches"


def test_la_despedida_va_con_el_saludo(archivo: Path) -> None:
    perfil.configurar("Eathan", archivo=archivo)

    manana = datetime(2026, 9, 1, 9)

    assert "Buenos días" in perfil.encabezar(archivo, manana)
    assert "buen día" in perfil.despedir(archivo, manana)


# --- Guardar y recordar -----------------------------------------------------


def test_al_principio_no_hay_perfil(archivo: Path) -> None:
    assert perfil.esta_configurado(archivo) is False


def test_se_configura_una_vez(archivo: Path) -> None:
    perfil.configurar("Eathan", nombre="Eathan Jiménez", archivo=archivo)

    assert perfil.esta_configurado(archivo) is True
    assert perfil.como_llamarte(archivo) == "Eathan"


def test_sobrevive_al_proceso(archivo: Path) -> None:
    perfil.configurar("jefe", archivo=archivo)

    assert perfil.cargar(archivo)["tratamiento"] == "jefe"


def test_sin_nombre_se_usa_el_trato(archivo: Path) -> None:
    perfil.configurar("Eathan", archivo=archivo)

    assert perfil.cargar(archivo)["nombre"] == "Eathan"


def test_recuerda_quien_lo_hizo(archivo: Path) -> None:
    perfil.configurar("Eathan", archivo=archivo)

    assert "Xentris" in perfil.quien_te_hizo(archivo)


def test_un_perfil_ilegible_no_impide_trabajar(archivo: Path) -> None:
    """Un JSON roto no puede dejar la herramienta inservible."""
    archivo.write_text("{esto no es json", encoding="utf-8")

    assert perfil.cargar(archivo) == {}
    assert perfil.esta_configurado(archivo) is False


def test_sin_perfil_igual_saluda(archivo: Path) -> None:
    """Con o sin nombre, la respuesta empieza y termina bien."""
    assert perfil.encabezar(archivo).endswith(".")


def test_no_guarda_credenciales(archivo: Path) -> None:
    """Es un perfil, no un almacén de secretos."""
    perfil.configurar("Eathan", archivo=archivo)

    guardado = archivo.read_text(encoding="utf-8").lower()

    for prohibido in ("key", "token", "password", "secret"):
        assert prohibido not in guardado


# --- La voz elegida ---------------------------------------------------------


def test_al_principio_no_hay_voz_elegida(archivo: Path) -> None:
    assert perfil.voz_preferida(archivo) == ""


def test_se_recuerda_la_que_eligio(archivo: Path) -> None:
    """Escuchó las dos y se quedó con una: eso no lo cambia que mañana
    aparezca otra."""
    perfil.configurar("Eathan", archivo=archivo)
    perfil.preferir_voz("openai", archivo)

    assert perfil.voz_preferida(archivo) == "openai"


def test_elegir_voz_no_borra_el_trato(archivo: Path) -> None:
    perfil.configurar("Eathan", archivo=archivo)
    perfil.preferir_voz("openai", archivo)

    assert perfil.como_llamarte(archivo) == "Eathan"
