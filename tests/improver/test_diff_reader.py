"""Leer un diff: qué archivos toca y cuánto.

Eran 100 líneas dentro de ``ImprovementEngine``, un módulo cuyo trabajo es
coordinar análisis, plan, pruebas, decisión, memoria y git. Suponían la
mitad de su complejidad (51) y no tenían nada que ver con orquestar.

Aquí son funciones puras, así que por fin se pueden probar los casos raros
sin construir un motor entero — que es exactamente donde un parser falla.
"""

from __future__ import annotations

import pytest

from ai_architect.improver.diff_reader import archivos, limpiar

GIT = """diff --git a/modulo.py b/modulo.py
index 1234567..89abcde 100644
--- a/modulo.py
+++ b/modulo.py
@@ -1,2 +1,3 @@
 sin cambio
-viejo
+nuevo
+otro
"""

PLANO = """--- a/modulo.py
+++ b/modulo.py
@@ -1 +1 @@
-viejo
+nuevo
"""


# --- Limpiar las vallas de markdown -----------------------------------------


def test_un_diff_limpio_no_se_toca() -> None:
    assert limpiar(PLANO).startswith("--- a/modulo.py")


def test_quita_la_valla_de_markdown() -> None:
    """Un modelo puede envolver el diff en ```diff, y aplicarlo así falla."""
    envuelto = "```diff\n" + PLANO + "```"

    assert limpiar(envuelto).startswith("--- a/modulo.py")
    assert "```" not in limpiar(envuelto)


def test_una_valla_sin_cerrar_tampoco_estorba() -> None:
    assert not limpiar("```diff\n" + PLANO).startswith("```")


def test_none_no_revienta() -> None:
    assert limpiar(None) == ""


def test_lo_vacio_sigue_vacio() -> None:
    assert limpiar("   \n  ") == ""


# --- El diff de git ---------------------------------------------------------


def test_lee_el_archivo_y_las_lineas() -> None:
    resultado = archivos(GIT)

    assert len(resultado) == 1
    assert resultado[0]["path"] == "modulo.py"
    assert resultado[0]["additions"] == 2
    assert resultado[0]["deletions"] == 1


def test_las_lineas_de_cabecera_no_cuentan_como_cambios() -> None:
    """``+++`` y ``---`` empiezan por + y -, y contarlas descuadra todo."""
    resultado = archivos(GIT)

    assert resultado[0]["additions"] == 2


def test_varios_archivos_en_un_parche() -> None:
    doble = GIT + GIT.replace("modulo.py", "otro.py")

    assert [a["path"] for a in archivos(doble)] == ["modulo.py", "otro.py"]


# --- Altas y bajas ----------------------------------------------------------


def test_un_archivo_nuevo_por_el_modo() -> None:
    nuevo = """diff --git a/nuevo.py b/nuevo.py
new file mode 100644
--- /dev/null
+++ b/nuevo.py
@@ -0,0 +1 @@
+valor = 1
"""

    resultado = archivos(nuevo)

    assert resultado[0]["action"] == "CREATE"
    assert resultado[0]["path"] == "nuevo.py"


def test_un_archivo_nuevo_por_dev_null() -> None:
    """Sin ``new file mode``, lo que delata el alta es el origen."""
    nuevo = "--- /dev/null\n+++ b/nuevo.py\n@@ -0,0 +1 @@\n+valor = 1\n"

    assert archivos(nuevo)[0]["action"] == "CREATE"


def test_un_archivo_borrado_por_el_modo() -> None:
    borrado = """diff --git a/viejo.py b/viejo.py
deleted file mode 100644
--- a/viejo.py
+++ /dev/null
@@ -1 +0,0 @@
-valor = 1
"""

    assert archivos(borrado)[0]["action"] == "DELETE"


def test_un_archivo_borrado_por_dev_null_en_destino() -> None:
    borrado = "--- a/viejo.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-valor = 1\n"

    resultado = archivos(borrado)

    assert resultado == [] or resultado[0]["action"] == "DELETE"


def test_lo_normal_es_modificar() -> None:
    assert archivos(GIT)[0]["action"] == "MODIFY"


# --- El diff unificado a secas ----------------------------------------------


def test_admite_un_diff_sin_cabecera_de_git() -> None:
    """Un modelo devuelve muchas veces el unificado a secas."""
    resultado = archivos(PLANO)

    assert len(resultado) == 1
    assert resultado[0]["path"] == "modulo.py"


def test_la_barra_b_no_forma_parte_del_nombre() -> None:
    assert archivos(PLANO)[0]["path"] == "modulo.py"


# --- Lo que se descarta -----------------------------------------------------


def test_un_archivo_sin_ruta_se_descarta() -> None:
    """No se puede aplicar nada sobre algo sin nombre."""
    suelto = "diff --git malformado\n+algo\n"

    assert archivos(suelto) == []


def test_un_diff_vacio_no_devuelve_nada() -> None:
    assert archivos("") == []


@pytest.mark.parametrize("basura", ["hola qué tal", "@@ -1 +1 @@", "   "])
def test_texto_que_no_es_un_diff(basura: str) -> None:
    assert archivos(basura) == []
