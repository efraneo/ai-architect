"""El arquitecto no leía ningún `.env`.

Se podía poner la clave del proveedor en el archivo que el propio
`.env.example` sugiere y `doctor` seguía diciendo `not_configured`:

    healthy: False
    status: degraded
    provider: not_configured        <- con la clave escrita en .env

Los proveedores solo miraban `os.getenv`, así que había que exportarla a
mano en cada sesión. Para alguien que quiere ejecutar la herramienta, eso es
la diferencia entre que funcione y que no.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.core import env_file
from ai_architect.core.env_file import cargar, leer, valor


@pytest.fixture
def sin_entorno():
    with mock.patch.dict(os.environ, {}, clear=True):
        yield


def escribir(tmp_path: Path, contenido: str) -> Path:
    archivo = tmp_path / ".env"
    archivo.write_text(contenido, encoding="utf-8")
    return archivo


# --- Cargar en el entorno ---------------------------------------------------


def test_carga_lo_que_declara(tmp_path: Path, sin_entorno) -> None:
    archivo = escribir(tmp_path, "OPENAI_API_KEY=sk-de-prueba\n")

    cargadas = cargar(archivo)

    assert cargadas == ["OPENAI_API_KEY"]
    assert os.environ["OPENAI_API_KEY"] == "sk-de-prueba"


def test_no_pisa_lo_ya_exportado(tmp_path: Path) -> None:
    """Quien escribe `OPENAI_API_KEY=... architect improve` lo hace a
    propósito: esa manda sobre la del archivo."""
    archivo = escribir(tmp_path, "OPENAI_API_KEY=del-archivo\n")

    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "del-entorno"}):
        cargadas = cargar(archivo)

        assert cargadas == []
        assert os.environ["OPENAI_API_KEY"] == "del-entorno"


def test_una_variable_vacia_no_cuenta_como_puesta(tmp_path: Path, sin_entorno) -> None:
    """La CI exporta las claves vacías a propósito; el archivo debe poder
    rellenarlas."""
    archivo = escribir(tmp_path, "OPENAI_API_KEY=sk-de-prueba\n")

    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
        cargar(archivo)

        assert os.environ["OPENAI_API_KEY"] == "sk-de-prueba"


def test_varias_a_la_vez(tmp_path: Path, sin_entorno) -> None:
    archivo = escribir(tmp_path, "UNA=1\nOTRA=2\nTERCERA=3\n")

    assert sorted(cargar(archivo)) == ["OTRA", "TERCERA", "UNA"]


def test_sin_archivo_no_carga_nada_ni_revienta(tmp_path: Path, sin_entorno) -> None:
    assert cargar(tmp_path / "no-existe") == []


def test_devuelve_los_nombres_nunca_los_valores(tmp_path: Path, sin_entorno) -> None:
    """Lo que se devuelve puede acabar impreso o en un log."""
    archivo = escribir(tmp_path, "SECRETO=no-me-imprimas\n")

    assert cargar(archivo) == ["SECRETO"]


# --- Lo que ya hacía, que sigue igual ---------------------------------------


def test_lee_pares(tmp_path: Path) -> None:
    assert leer(escribir(tmp_path, "A=1\nB=2\n")) == {"A": "1", "B": "2"}


def test_el_entorno_manda_sobre_el_archivo(tmp_path: Path) -> None:
    archivo = escribir(tmp_path, "A=del-archivo\n")

    with mock.patch.dict(os.environ, {"A": "del-entorno"}):
        assert valor("A", archivo) == "del-entorno"


# --- Que la clave no dependa de desde dónde llames --------------------------
#
# Lanzando el arquitecto con un `.cmd` desde otra carpeta, el `.env` del
# repositorio quedaba fuera de alcance y el proveedor contestaba
# `not_configured` teniendo la clave escrita a dos carpetas de distancia.


def test_carga_el_env_del_proyecto_aunque_no_sea_el_directorio_actual(
    tmp_path, monkeypatch
) -> None:
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (proyecto / ".env").write_text("CLAVE_DEL_PROYECTO=si\n", encoding="utf-8")

    otra = tmp_path / "otra"
    otra.mkdir()
    monkeypatch.chdir(otra)
    monkeypatch.delenv("CLAVE_DEL_PROYECTO", raising=False)

    env_file.cargar_todo(proyecto)

    assert os.environ["CLAVE_DEL_PROYECTO"] == "si"


def test_el_del_directorio_actual_manda_sobre_el_del_proyecto(
    tmp_path, monkeypatch
) -> None:
    """Estar dentro de una carpeta es decir que esa es la de esta sesión."""
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    (proyecto / ".env").write_text("QUIEN=proyecto\n", encoding="utf-8")

    aqui = tmp_path / "aqui"
    aqui.mkdir()
    (aqui / ".env").write_text("QUIEN=sesion\n", encoding="utf-8")

    monkeypatch.chdir(aqui)
    monkeypatch.delenv("QUIEN", raising=False)

    env_file.cargar_todo(proyecto)

    assert os.environ["QUIEN"] == "sesion"


def test_lo_exportado_a_mano_manda_sobre_los_tres(tmp_path, monkeypatch) -> None:
    (tmp_path / ".env").write_text("QUIEN=archivo\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QUIEN", "a-mano")

    env_file.cargar_todo()

    assert os.environ["QUIEN"] == "a-mano"


def test_una_carpeta_que_no_existe_no_revienta(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert env_file.cargar_todo(tmp_path / "no-existe") == []


def test_la_raiz_del_paquete_es_la_del_repositorio() -> None:
    """De ahí sale el `.env` cuando se llama desde cualquier otro sitio."""
    raiz = env_file.raiz_del_paquete()

    assert (raiz / "ai_architect").is_dir()
    assert (raiz / "pyproject.toml").is_file()
