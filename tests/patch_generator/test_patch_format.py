"""El formato del contenedor de parches, sin tocar el disco.

`PatchLoader` mezclaba dos trabajos: abrir un archivo y entender su formato.
El segundo eran 300 líneas y con ellas el módulo llegaba a complejidad 24.

Separado, el formato se prueba dándole texto —que es donde un parser falla—
en vez de escribir un archivo primero para cada caso.
"""

from __future__ import annotations

import pytest

from ai_architect.patch_generator.patch_format import (
    extraer_diff,
    leer_aprobado,
    leer_archivo,
    leer_cabecera,
    valor_de,
)

CABECERA = """ID: abc123
TITLE: Un parche
DESCRIPTION: Lo que hace
CREATED: 2026-09-01T10:00:00
APPROVED: true

FILES
-----
MODIFY modulo.py 7 3
CREATE nuevo.py 12 0

diff --git a/modulo.py b/modulo.py
--- a/modulo.py
+++ b/modulo.py
"""


# --- La cabecera ------------------------------------------------------------


def test_lee_los_metadatos() -> None:
    metadata, _ = leer_cabecera(CABECERA)

    assert metadata["id"] == "abc123"
    assert metadata["title"] == "Un parche"
    assert metadata["created"] == "2026-09-01T10:00:00"


def test_lee_la_tabla_de_archivos() -> None:
    _, archivos = leer_cabecera(CABECERA)

    assert [a.path for a in archivos] == ["modulo.py", "nuevo.py"]
    assert archivos[0].additions == 7
    assert archivos[0].deletions == 3


def test_la_cabecera_termina_donde_empieza_el_diff() -> None:
    """Si siguiera leyendo, las líneas del parche entrarían como archivos."""
    _, archivos = leer_cabecera(CABECERA)

    assert len(archivos) == 2


def test_la_linea_de_guiones_no_es_un_archivo() -> None:
    _, archivos = leer_cabecera(CABECERA)

    assert all(a.path for a in archivos)


def test_un_texto_sin_cabecera() -> None:
    metadata, archivos = leer_cabecera("diff --git a/x b/x\n+algo\n")

    assert metadata == {}
    assert archivos == []


# --- Una fila de la tabla ---------------------------------------------------


def test_el_formato_actual() -> None:
    archivo = leer_archivo("MODIFY ruta/al/modulo.py 7 3")

    assert archivo is not None
    assert archivo.path == "ruta/al/modulo.py"
    assert archivo.action == "MODIFY"
    assert archivo.additions == 7
    assert archivo.deletions == 3


def test_el_formato_antiguo_sin_contadores() -> None:
    """Los parches viejos siguen cargando, con los contadores a cero."""
    archivo = leer_archivo("MODIFY modulo.py")

    assert archivo is not None
    assert archivo.path == "modulo.py"
    assert archivo.additions == 0


def test_una_ruta_con_espacios() -> None:
    """Los contadores se leen desde el final, no por posición."""
    archivo = leer_archivo("MODIFY carpeta con espacios/x.py 5 2")

    assert archivo is not None
    assert archivo.path == "carpeta con espacios/x.py"
    assert archivo.additions == 5


def test_si_los_ultimos_campos_no_son_numeros_todo_es_ruta() -> None:
    archivo = leer_archivo("MODIFY una ruta rara sin numeros")

    assert archivo is not None
    assert archivo.path == "una ruta rara sin numeros"


@pytest.mark.parametrize("linea", ["", "MODIFY", "   "])
def test_una_fila_incompleta_se_descarta(linea: str) -> None:
    assert leer_archivo(linea) is None


# --- El diff ----------------------------------------------------------------


def test_extrae_el_diff_desde_su_cabecera() -> None:
    assert extraer_diff(CABECERA).startswith("diff --git a/modulo.py")


def test_conserva_los_saltos_finales() -> None:
    """Partir en líneas y volver a unirlas los destruiría, y un parche que
    termina en uno o en tres no es el mismo para ``git apply``."""
    texto = "ID: x\n\ndiff --git a/x b/x\n+uno\n\n\n"

    assert extraer_diff(texto).endswith("+uno\n\n\n")


def test_sin_diff_devuelve_vacio() -> None:
    assert extraer_diff("ID: x\nTITLE: y\n") == ""


# --- La aprobación ----------------------------------------------------------


@pytest.mark.parametrize("valor", ["true", "TRUE", " yes ", "1", "approved"])
def test_lo_que_cuenta_como_aprobado(valor: str) -> None:
    assert leer_aprobado(valor) is True


@pytest.mark.parametrize("valor", ["false", "no", "0", "", "quizá"])
def test_lo_que_no(valor: str) -> None:
    assert leer_aprobado(valor) is False


def test_sin_metadata_no_esta_aprobado() -> None:
    """Un parche antiguo no puede volverse ejecutable solo por cargarlo."""
    assert leer_aprobado(None) is False


# --- El valor de una línea --------------------------------------------------


def test_el_valor_va_despues_del_primer_dos_puntos() -> None:
    assert valor_de("TITLE: Con: dos puntos dentro") == "Con: dos puntos dentro"


def test_una_linea_sin_dos_puntos() -> None:
    assert valor_de("TITLE sin nada") == ""
