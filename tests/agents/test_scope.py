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
    recorrido_compartido,
    todo,
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


# --- Un solo recorrido para todos -------------------------------------------


def test_sin_bloque_cada_llamada_recorre_de_nuevo(proyecto: Path) -> None:
    """Fuera del bloque no hay caché: los archivos pueden haber cambiado."""
    primera = archivos_py(proyecto)

    (proyecto / "nuevo.py").write_text("x = 1\n", encoding="utf-8")

    assert len(archivos_py(proyecto)) == len(primera) + 1


def test_dentro_del_bloque_se_recorre_una_vez(proyecto: Path) -> None:
    """Once agentes recorrían el mismo árbol seis veces."""
    with recorrido_compartido():
        primera = archivos_py(proyecto)

        (proyecto / "nuevo.py").write_text("x = 1\n", encoding="utf-8")

        assert archivos_py(proyecto) == primera


def test_al_salir_del_bloque_el_cache_se_tira(proyecto: Path) -> None:
    with recorrido_compartido():
        archivos_py(proyecto)

    (proyecto / "nuevo.py").write_text("x = 1\n", encoding="utf-8")

    assert any(f.name == "nuevo.py" for f in archivos_py(proyecto))


def test_una_excepcion_tampoco_deja_el_cache_puesto(proyecto: Path) -> None:
    """Si se quedara puesto, la siguiente inspección vería datos viejos."""
    with pytest.raises(RuntimeError):
        with recorrido_compartido():
            archivos_py(proyecto)
            raise RuntimeError("algo")

    (proyecto / "nuevo.py").write_text("x = 1\n", encoding="utf-8")

    assert any(f.name == "nuevo.py" for f in archivos_py(proyecto))


def test_los_bloques_se_pueden_anidar(proyecto: Path) -> None:
    """Solo el de fuera crea y destruye el caché."""
    with recorrido_compartido():
        with recorrido_compartido():
            archivos_py(proyecto)

        # El bloque interior no debe haber tirado el caché del exterior.
        (proyecto / "nuevo.py").write_text("x = 1\n", encoding="utf-8")

        assert not any(f.name == "nuevo.py" for f in archivos_py(proyecto))


def test_cada_patron_tiene_su_propia_entrada(proyecto: Path) -> None:
    with recorrido_compartido():
        assert [f.name for f in archivos_py(proyecto)] == ["modulo.py"]
        assert {f.name for f in archivos(proyecto)} == {"modulo.py", "README.md"}


# --- todo(): con carpetas y binarios ----------------------------------------


def test_todo_incluye_las_carpetas(proyecto: Path) -> None:
    """Las métricas cuentan carpetas."""
    (proyecto / "src").mkdir()

    assert any(entrada.name == "src" for entrada in todo(proyecto))


def test_todo_incluye_los_binarios_del_proyecto(proyecto: Path) -> None:
    """Una imagen ocupa espacio y forma parte del proyecto."""
    (proyecto / "logo.png").write_bytes(b"\x89PNG")

    assert any(entrada.name == "logo.png" for entrada in todo(proyecto))


def test_todo_sigue_sin_mirar_el_venv(proyecto: Path) -> None:
    assert not any(".venv" in entrada.parts for entrada in todo(proyecto))
