"""The agents look at the project -- not at its dependencies.

Every agent walked the tree with a bare ``rglob``, so on this repository the
Security Agent reported fifteen leaked secrets: all fifteen inside
``.venv``, including binaries like ``ruff.exe`` where the regex matched raw
bytes.

Those findings reach the decision engine. An agent that reports someone
else's dependencies does not help: it lies with numbers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect.agents.scope import (
    archivos,
    archivos_py,
    es_binario,
    esta_ignorado,
)


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    """A project with its own code and a virtualenv beside it."""
    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# hola\n", encoding="utf-8")

    paquete = tmp_path / ".venv" / "Lib" / "site-packages" / "httpx"
    paquete.mkdir(parents=True)
    (paquete / "_urls.py").write_text("password = 'x'\n", encoding="utf-8")

    (tmp_path / ".venv" / "Scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".venv" / "Scripts" / "ruff.exe").write_bytes(b"\x00binario")

    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "modulo.cpython-312.pyc").write_bytes(b"\x00")

    return tmp_path


# --- Lo que hay que ignorar -------------------------------------------------


def test_lo_de_dentro_del_venv_se_ignora(proyecto: Path) -> None:
    hondo = proyecto / ".venv" / "Lib" / "site-packages" / "httpx" / "_urls.py"

    assert esta_ignorado(hondo, proyecto) is True


def test_se_mira_la_ruta_entera_no_solo_la_carpeta_padre(proyecto: Path) -> None:
    """The regression: ``.venv`` sits four levels above the file."""
    hondo = proyecto / ".venv" / "Lib" / "site-packages" / "httpx" / "_urls.py"

    assert hondo.parent.name not in {".venv", "node_modules"}
    assert esta_ignorado(hondo, proyecto) is True


def test_el_codigo_del_proyecto_no_se_ignora(proyecto: Path) -> None:
    assert esta_ignorado(proyecto / "modulo.py", proyecto) is False


def test_las_cachés_tampoco_cuentan(proyecto: Path) -> None:
    archivo = proyecto / "__pycache__" / "modulo.cpython-312.pyc"

    assert esta_ignorado(archivo, proyecto) is True


def test_una_ruta_fuera_de_la_raiz_no_revienta(proyecto: Path) -> None:
    """``relative_to`` raises; the filter has to survive it."""
    assert esta_ignorado(Path("C:/otro/sitio/x.py"), proyecto) is False


# --- Los binarios -----------------------------------------------------------


@pytest.mark.parametrize("nombre", ["ruff.exe", "x.pyd", "y.so", "z.pyc", "a.png"])
def test_los_binarios_se_reconocen(nombre: str) -> None:
    """Read as text they are bytes, and a regex matches anything in bytes."""
    assert es_binario(Path(nombre)) is True


@pytest.mark.parametrize("nombre", ["modulo.py", "README.md", "config.toml"])
def test_el_texto_no_es_binario(nombre: str) -> None:
    assert es_binario(Path(nombre)) is False


# --- El recorrido -----------------------------------------------------------


def test_solo_devuelve_los_archivos_del_proyecto(proyecto: Path) -> None:
    nombres = {f.name for f in archivos(proyecto)}

    assert nombres == {"modulo.py", "README.md"}


def test_no_devuelve_carpetas(proyecto: Path) -> None:
    assert all(f.is_file() for f in archivos(proyecto))


def test_los_py_del_proyecto_no_incluyen_los_del_venv(proyecto: Path) -> None:
    """There were two ``.py`` files: only one belongs to the project."""
    assert [f.name for f in archivos_py(proyecto)] == ["modulo.py"]


def test_un_proyecto_vacio_no_devuelve_nada(tmp_path: Path) -> None:
    assert archivos_py(tmp_path) == []
