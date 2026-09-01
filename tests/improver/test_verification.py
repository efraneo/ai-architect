"""Modificar, ejecutar, y deshacer si empeora.

El fallo que esto arregla, comprobado sobre un proyecto de juguete antes de
tocar nada:

    un parche que rompe suma(2,2) de 4 a 0
    -> tests_ok que recibió la decisión: True

Las pruebas se ejecutaban **antes** de aplicar el parche, así que
``tests_ok`` significaba "el repositorio estaba en verde", no "el cambio es
bueno". El motor de decisión juzgaba un código que no era el que iba a
quedar.

El ciclo era *ejecutar -> modificar*. Ahora es *modificar -> ejecutar ->
deshacer si empeora*.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ai_architect.improver.verification import peor_que, verificar

BUENO = """--- a/modulo.py
+++ b/modulo.py
@@ -1,2 +1,2 @@
 def suma(a, b):
-    return a + b
+    return b + a
"""

ROTO = """--- a/modulo.py
+++ b/modulo.py
@@ -1,2 +1,2 @@
 def suma(a, b):
-    return a + b
+    return a - b
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

    (tmp_path / "modulo.py").write_text(
        "def suma(a, b):\n    return a + b\n",
        encoding="utf-8",
    )

    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "base")

    return tmp_path


def pruebas(ok: bool = True, fallos: int = 0, ejecutadas: bool = True) -> dict:
    return {"executed": ejecutadas, "success": ok, "passed": 1, "failed": fallos}


def suite(resultados: list[dict]):
    """Una suite falsa que devuelve un resultado distinto en cada llamada."""
    restantes = list(resultados)

    def ejecutar(_repositorio):
        return restantes.pop(0)

    return ejecutar


# --- Qué cuenta como empeorar -----------------------------------------------


def test_romper_lo_que_funcionaba_es_empeorar() -> None:
    assert peor_que(pruebas(ok=False, fallos=1), pruebas(ok=True)) is True


def test_aumentar_los_fallos_es_empeorar() -> None:
    antes = pruebas(ok=False, fallos=2)
    despues = pruebas(ok=False, fallos=5)

    assert peor_que(despues, antes) is True


def test_un_repositorio_que_ya_venia_en_rojo_no_condena_al_parche() -> None:
    """Si ya fallaban tres pruebas antes, seguir fallando tres no es culpa
    del cambio."""
    antes = pruebas(ok=False, fallos=3)
    despues = pruebas(ok=False, fallos=3)

    assert peor_que(despues, antes) is False


def test_arreglar_fallos_no_es_empeorar() -> None:
    antes = pruebas(ok=False, fallos=3)
    despues = pruebas(ok=True, fallos=0)

    assert peor_que(despues, antes) is False


def test_sin_pruebas_ejecutadas_no_se_juzga() -> None:
    """Sin medición no hay veredicto: inventarlo sería el fallo de siempre."""
    assert peor_que(pruebas(ok=False), pruebas(ejecutadas=False)) is False
    assert peor_que(pruebas(ejecutadas=False), pruebas(ok=True)) is False


# --- El ciclo completo ------------------------------------------------------


def test_un_cambio_bueno_se_queda(repo: Path) -> None:
    resultado = verificar(repo, BUENO, pruebas(), suite([pruebas()]))

    assert resultado["applied"] is True
    assert resultado["reverted"] is False
    assert "return b + a" in (repo / "modulo.py").read_text(encoding="utf-8")


def test_un_cambio_que_rompe_se_deshace(repo: Path) -> None:
    """La regresión entera: antes ni se aplicaba ni se medía."""
    resultado = verificar(
        repo,
        ROTO,
        pruebas(ok=True),
        suite([pruebas(ok=False, fallos=1)]),
    )

    assert resultado["applied"] is True
    assert resultado["reverted"] is True
    assert "rompe las pruebas" in resultado["reason"]
    assert "return a + b" in (repo / "modulo.py").read_text(encoding="utf-8")


def test_las_pruebas_del_resultado_son_las_de_despues(repo: Path) -> None:
    """Lo que va al motor de decisión tiene que ser el estado final, no el
    inicial: era exactamente el fallo."""
    resultado = verificar(
        repo,
        ROTO,
        pruebas(ok=True),
        suite([pruebas(ok=False, fallos=1)]),
    )

    assert resultado["tests_before"]["success"] is True
    assert resultado["tests"]["success"] is False


# --- Cuando no se llega a aplicar -------------------------------------------


def test_un_parche_vacio_no_toca_nada(repo: Path) -> None:
    resultado = verificar(repo, "   \n", pruebas(), suite([]))

    assert resultado["applied"] is False
    assert "vacío" in resultado["reason"]


def test_un_parche_que_no_encaja(repo: Path) -> None:
    (repo / "modulo.py").write_text("otra cosa\n", encoding="utf-8")

    resultado = verificar(repo, BUENO, pruebas(), suite([]))

    assert resultado["applied"] is False
    assert resultado["reverted"] is False


def test_si_no_se_aplica_las_pruebas_siguen_siendo_las_de_antes(
    repo: Path,
) -> None:
    antes = pruebas(ok=True)

    resultado = verificar(repo, "", antes, suite([]))

    assert resultado["tests"] == antes


def test_fuera_de_un_repositorio_git_no_se_aplica(tmp_path: Path) -> None:
    suelta = tmp_path / "suelta"
    suelta.mkdir()
    (suelta / "modulo.py").write_text("def suma(a, b):\n    return a + b\n", "utf-8")

    resultado = verificar(suelta, BUENO, pruebas(), suite([]))

    assert resultado["applied"] is False
    assert "Git repository" in resultado["reason"]
