"""Aplicar un parche con git, y contar qué pasó.

Eran 130 líneas dentro de `ExecutionPipeline`, que coordina validación,
aplicación, verificación y rollback. Hacían cuatro cosas —comprobar el
destino, comprobar que es un repositorio, escribir el temporal y ejecutar
`git apply`— y eran casi toda su complejidad.

Separadas, se pueden probar los caminos de fallo que antes no se alcanzaban
sin montar un pipeline entero: git sin instalar, un destino que no es un
repositorio, un diff vacío.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.execution.git_apply import SIN_GIT, aplicar, error

DIFF = """diff --git a/modulo.py b/modulo.py
--- a/modulo.py
+++ b/modulo.py
@@ -1 +1 @@
-valor = 1
+valor = 2
"""


def git(repo: Path, *argumentos: str) -> None:
    subprocess.run(
        ["git", *argumentos],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-b", "principal")
    git(tmp_path, "config", "user.email", "prueba@ejemplo.com")
    git(tmp_path, "config", "user.name", "Prueba")

    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")

    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "primero")

    return tmp_path


# --- El camino feliz --------------------------------------------------------


def test_aplica_el_parche(repo: Path) -> None:
    resultado = aplicar(repo, DIFF)

    assert resultado["success"] is True
    assert resultado["message"] == "Patch applied successfully."
    assert (repo / "modulo.py").read_text(encoding="utf-8") == "valor = 2\n"


def test_check_only_no_toca_nada(repo: Path) -> None:
    resultado = aplicar(repo, DIFF, check_only=True)

    assert resultado["success"] is True
    assert resultado["message"] == "Patch validation succeeded."
    assert (repo / "modulo.py").read_text(encoding="utf-8") == "valor = 1\n"


def test_reverse_lo_deshace(repo: Path) -> None:
    aplicar(repo, DIFF)

    resultado = aplicar(repo, DIFF, reverse=True)

    assert resultado["success"] is True
    assert (repo / "modulo.py").read_text(encoding="utf-8") == "valor = 1\n"


def test_un_diff_sin_salto_final_tambien_aplica(repo: Path) -> None:
    """``git apply`` rechaza un parche sin salto final, y un modelo lo
    devuelve así la mitad de las veces."""
    resultado = aplicar(repo, DIFF.rstrip("\n"))

    assert resultado["success"] is True


# --- Lo que git rechaza -----------------------------------------------------


def test_un_parche_que_no_encaja(repo: Path) -> None:
    (repo / "modulo.py").write_text("otra cosa\n", encoding="utf-8")

    resultado = aplicar(repo, DIFF)

    assert resultado["success"] is False
    assert resultado["message"] == "Git rejected the patch."
    assert resultado["returncode"] != 0


def test_el_rechazo_trae_lo_que_dijo_git(repo: Path) -> None:
    (repo / "modulo.py").write_text("otra cosa\n", encoding="utf-8")

    assert aplicar(repo, DIFF)["stderr"]


# --- Lo que se comprueba antes de molestar a git ----------------------------


def test_un_destino_que_no_existe(tmp_path: Path) -> None:
    resultado = aplicar(tmp_path / "no-existe", DIFF)

    assert resultado["success"] is False
    assert "does not exist" in resultado["message"]


def test_un_destino_que_es_un_archivo(tmp_path: Path) -> None:
    archivo = tmp_path / "archivo.txt"
    archivo.write_text("x", encoding="utf-8")

    assert "not a directory" in aplicar(archivo, DIFF)["message"]


def test_un_diff_vacio(repo: Path) -> None:
    assert "no unified diff" in aplicar(repo, "   \n  ")["message"]


def test_una_carpeta_que_no_es_repositorio(tmp_path: Path) -> None:
    suelta = tmp_path / "suelta"
    suelta.mkdir()

    resultado = aplicar(suelta, DIFF)

    assert resultado["success"] is False
    assert "not a Git repository" in resultado["message"]


# --- Los fallos del entorno -------------------------------------------------


def test_sin_git_instalado(repo: Path) -> None:
    """Antes este camino no se podía probar sin montar un pipeline."""
    with mock.patch("subprocess.run", side_effect=FileNotFoundError):
        resultado = aplicar(repo, DIFF)

    assert resultado["success"] is False
    assert resultado["returncode"] == SIN_GIT
    assert "PATH" in resultado["message"]


def test_si_git_se_queda_colgado(repo: Path) -> None:
    """Sin tiempo límite, un `git apply` colgado colgaba la ejecución
    entera. Antes no había ninguno."""
    with mock.patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="git", timeout=120),
    ):
        resultado = aplicar(repo, DIFF)

    assert resultado["success"] is False
    assert "did not finish" in resultado["message"]


def test_un_error_del_sistema_operativo(repo: Path) -> None:
    with mock.patch("subprocess.run", side_effect=OSError("disco lleno")):
        resultado = aplicar(repo, DIFF)

    assert resultado["success"] is False
    assert "disco lleno" in resultado["stderr"]


def test_nunca_lanza(repo: Path) -> None:
    """Quien llama tiene que poder decidir con el resultado en la mano."""
    for fallo in (FileNotFoundError, OSError("x")):
        with mock.patch("subprocess.run", side_effect=fallo):
            assert aplicar(repo, DIFF)["success"] is False


# --- El temporal no se queda ------------------------------------------------


def test_el_temporal_se_borra(repo: Path, tmp_path: Path) -> None:
    creados: list[Path] = []

    import ai_architect.execution.git_apply as modulo

    original = modulo._escribir

    def espiar(diff: str) -> Path:
        ruta = original(diff)
        creados.append(ruta)
        return ruta

    with mock.patch.object(modulo, "_escribir", espiar):
        aplicar(repo, DIFF)

    assert creados
    assert not creados[0].exists()


# --- La forma del error -----------------------------------------------------


def test_el_error_tiene_la_forma_de_un_resultado() -> None:
    """Quien lo recibe no debería tener que distinguir de dónde vino."""
    resultado = error("algo pasó")

    assert set(resultado) == {
        "success",
        "message",
        "stdout",
        "stderr",
        "returncode",
    }
    assert resultado["success"] is False
