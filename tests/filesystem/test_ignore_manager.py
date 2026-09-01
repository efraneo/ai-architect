"""Los agentes respetan ahora el ``.gitignore`` del proyecto.

``IgnoreManager`` estaba huérfano y era la misma lista fija que ya tenía
``constants.py``. Al compararla con el ``.gitignore`` de este repositorio
salió el hueco:

    ignorados por git pero NO por los agentes:
    htmlcov, .ai_architect, workspace, memory/db, ...

Cada proyecto ignora sus propias carpetas de salida, y los agentes las
recorrían todas: el mismo problema del ``.venv``, pero en proyectos ajenos.

**La regla clave está en el último bloque**: solo se aplica a carpetas. Un
archivo ignorado por git puede ser justo donde hay que mirar — ``.env`` es
el sitio más probable de una clave filtrada.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect.agents.scope import archivos_py, esta_ignorado
from ai_architect.filesystem.ignore_manager import (
    IgnoreManager,
    leer_carpetas_ignoradas,
)


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    (tmp_path / "modulo.py").write_text("x = 1\n", encoding="utf-8")
    return tmp_path


def con_gitignore(raiz: Path, contenido: str) -> Path:
    (raiz / ".gitignore").write_text(contenido, encoding="utf-8")
    return raiz


# --- Leer el .gitignore -----------------------------------------------------


def test_una_carpeta_con_barra(tmp_path: Path) -> None:
    con_gitignore(tmp_path, "target/\n")

    assert leer_carpetas_ignoradas(tmp_path / ".gitignore") == {"target"}


def test_un_nombre_sin_extension_cuenta_como_carpeta(tmp_path: Path) -> None:
    con_gitignore(tmp_path, "htmlcov\n")

    assert leer_carpetas_ignoradas(tmp_path / ".gitignore") == {"htmlcov"}


def test_varias_carpetas(tmp_path: Path) -> None:
    con_gitignore(tmp_path, "target/\nout/\ndist/\n")

    assert leer_carpetas_ignoradas(tmp_path / ".gitignore") == {
        "target",
        "out",
        "dist",
    }


def test_los_comentarios_y_las_vacias_no_cuentan(tmp_path: Path) -> None:
    con_gitignore(tmp_path, "# salida\n\ntarget/\n")

    assert leer_carpetas_ignoradas(tmp_path / ".gitignore") == {"target"}


def test_sin_gitignore_no_hay_nada_que_leer(tmp_path: Path) -> None:
    assert leer_carpetas_ignoradas(tmp_path / ".gitignore") == set()


# --- Lo que NO se interpreta ------------------------------------------------


@pytest.mark.parametrize(
    "patron",
    ["*.log", "!importante/", "docs/build/", "temp?/", "[abc]/"],
)
def test_lo_que_no_se_entiende_se_descarta(tmp_path: Path, patron: str) -> None:
    """Interpretar a medias sería peor que no leerlo: se acabaría dejando
    fuera código que sí es del proyecto."""
    con_gitignore(tmp_path, patron + "\n")

    assert leer_carpetas_ignoradas(tmp_path / ".gitignore") == set()


def test_un_archivo_con_extension_no_es_una_carpeta(tmp_path: Path) -> None:
    """``.env`` y ``.coverage`` no son carpetas, y no deben excluirse."""
    con_gitignore(tmp_path, ".env\n.coverage\ncoverage.xml\n")

    assert leer_carpetas_ignoradas(tmp_path / ".gitignore") == set()


# --- El gestor --------------------------------------------------------------


def test_sin_gitignore_manda_la_lista_de_siempre(tmp_path: Path) -> None:
    gestor = IgnoreManager.for_project(tmp_path)

    assert gestor.should_ignore(Path(".venv/lib/x.py")) is True
    assert gestor.should_ignore(Path("modulo.py")) is False


def test_con_gitignore_se_suma_lo_del_proyecto(tmp_path: Path) -> None:
    con_gitignore(tmp_path, "target/\n")

    gestor = IgnoreManager.for_project(tmp_path)

    assert gestor.should_ignore(Path("target/generado.py")) is True
    assert gestor.should_ignore(Path(".venv/lib/x.py")) is True


def test_la_lista_de_siempre_no_se_pierde(tmp_path: Path) -> None:
    con_gitignore(tmp_path, "target/\n")

    directorios = IgnoreManager.for_project(tmp_path).export()["directories"]

    assert "target" in directorios
    assert ".venv" in directorios
    assert "node_modules" in directorios


# --- Integrado con los agentes ----------------------------------------------


def test_una_carpeta_del_proyecto_deja_de_recorrerse(proyecto: Path) -> None:
    salida = proyecto / "target"
    salida.mkdir()
    (salida / "generado.py").write_text("y = 2\n", encoding="utf-8")

    assert len(archivos_py(proyecto)) == 2

    con_gitignore(proyecto, "target/\n")

    assert [f.name for f in archivos_py(proyecto)] == ["modulo.py"]


def test_el_env_sigue_visible(proyecto: Path) -> None:
    """La regla que más importa: git ignora ``.env`` en casi todos los
    proyectos, y es **exactamente** donde el agente de seguridad tiene que
    mirar para encontrar una clave filtrada."""
    con_gitignore(proyecto, ".env\n")

    (proyecto / ".env").write_text("SECRET=abc\n", encoding="utf-8")

    assert esta_ignorado(proyecto / ".env", proyecto) is False


def test_editar_el_gitignore_se_nota(proyecto: Path) -> None:
    """El gestor se cachea por fecha del archivo: sin invalidación, cambiar
    el ``.gitignore`` no surtiría efecto hasta reiniciar."""
    salida = proyecto / "target"
    salida.mkdir()
    (salida / "generado.py").write_text("y = 2\n", encoding="utf-8")

    con_gitignore(proyecto, "# nada\n")
    assert len(archivos_py(proyecto)) == 2

    import os
    import time

    time.sleep(0.01)
    con_gitignore(proyecto, "target/\n")
    os.utime(proyecto / ".gitignore", None)

    assert len(archivos_py(proyecto)) == 1
