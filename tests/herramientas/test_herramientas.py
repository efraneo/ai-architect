"""Herramientas: que los agentes comprueben en vez de suponer.

Un agente que solo lee texto dice "hay librerías desactualizadas" y "hay
una contraseña". Lo primero vale para cualquier proyecto de más de un año;
lo segundo no distingue un secreto en disco de uno commiteado, que son dos
problemas con dos arreglos distintos.

Ninguna prueba sale a internet.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.herramientas import cve, historial

# =========================================================
# CVE
# =========================================================


def test_lee_las_dependencias_declaradas(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "openai>=1.40.0\nrequests==2.32.3\n# un comentario\nflask~=3.0\n"
    )

    encontradas = dict(cve.dependencias(tmp_path))

    assert encontradas["openai"] == "1.40.0"
    assert encontradas["requests"] == "2.32.3"
    assert encontradas["flask"] == "3.0"


def test_los_comentarios_no_son_dependencias(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("# numpy>=2.0\nopenai>=1.0\n")

    assert "numpy" not in dict(cve.dependencias(tmp_path))


def test_sin_dependencias_no_pregunta_a_nadie(tmp_path: Path) -> None:
    with mock.patch.object(cve, "_preguntar") as preguntar:
        salida = cve.revisar(tmp_path)

    preguntar.assert_not_called()
    assert salida["consultado"] == 0


def test_devuelve_los_fallos_de_cada_paquete(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("gitpython>=3.1.43\n")

    with mock.patch.object(
        cve, "_preguntar", return_value=[{"vulns": [{"id": "GHSA-2f96"}]}]
    ):
        with mock.patch.object(cve, "_detallar", return_value=[]):
            salida = cve.revisar(tmp_path)

    assert salida["vulnerables"][0]["paquete"] == "gitpython"
    assert salida["vulnerables"][0]["fallos"] == ["GHSA-2f96"]


def test_sin_red_no_dice_que_esta_todo_bien(tmp_path: Path) -> None:
    """Contestar "ninguna vulnerabilidad" sin haber preguntado es peor que
    no contestar: parece una respuesta y no lo es."""
    (tmp_path / "requirements.txt").write_text("openai>=1.0\n")

    with mock.patch.object(cve, "_preguntar", return_value=None):
        salida = cve.revisar(tmp_path)

    assert salida["vulnerables"] == []
    assert "no pude consultar" in salida["nota"]


def test_se_avisa_de_que_son_versiones_declaradas(tmp_path: Path) -> None:
    """Un `>=1.40.0` no dice qué hay instalado: dice el peor caso aceptado."""
    (tmp_path / "requirements.txt").write_text("openai>=1.0\n")

    with mock.patch.object(cve, "_preguntar", return_value=[{}]):
        salida = cve.revisar(tmp_path)

    assert "declaradas, no instaladas" in salida["nota"]


def test_la_gravedad_se_dice_en_una_palabra() -> None:
    """Un vector CVSS es exacto y no lo entiende nadie de oído."""
    alta = cve._gravedad({"severity": [{"score": "CVSS:3.1/AV:N/AC:L/C:H/I:H"}]})

    assert alta == "alta"
    assert cve._gravedad({}) == "sin clasificar"


# =========================================================
# Historial
# =========================================================


HISTORIA = """commit abc12345def
Author: alguien
    puso la clave

diff --git a/config.py b/config.py
+++ b/config.py
+PASSWORD = "correcthorsebattery"
+algo_normal = 1

commit fed54321cba
Author: alguien
    ejemplo en el README

+++ b/README.md
+Pon tu clave: sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
-PASSWORD = "correcthorsebattery"
"""


def test_encuentra_un_secreto_commiteado() -> None:
    hallazgos = historial._buscar(HISTORIA)

    assert any(h["tipo"] == "contraseña escrita" for h in hallazgos)


def test_dice_en_que_commit() -> None:
    """Sin el commit no se puede ir a mirarlo."""
    hallazgos = historial._buscar(HISTORIA)

    assert hallazgos[0]["commit"] == "abc12345"


def test_nunca_reproduce_el_secreto() -> None:
    """Un informe que repite la clave la filtra otra vez, en un sitio nuevo."""
    hallazgos = historial._buscar(HISTORIA)

    for hallazgo in hallazgos:
        assert "correcthorsebattery" not in hallazgo["muestra"]
        assert "«oculto»" in hallazgo["muestra"]


def test_un_ejemplo_de_la_documentacion_no_cuenta() -> None:
    """Sin esto, cada README con "pon tu clave aquí" es una filtración."""
    hallazgos = historial._buscar(HISTORIA)

    assert not any("sk-proj-xxx" in h["muestra"] for h in hallazgos)


def test_solo_las_lineas_anadidas() -> None:
    """Una línea borrada aquí es una que se añadió en otro commit."""
    hallazgos = historial._buscar(HISTORIA)

    assert len(hallazgos) == 1, "la línea con `-` no se cuenta otra vez"


@pytest.mark.parametrize(
    ("nombre", "linea"),
    [
        ("clave de OpenAI", "+KEY = sk-abcdefghijklmnopqrstuvwxyz123456"),
        # Sin "EXAMPLE" dentro: el filtro de falsos positivos lo tumbaba,
        # que es justo lo que tiene que hacer.
        ("clave de AWS", "+aws = AKIA3F7QWERTYUIOPLKJ"),
        ("clave privada", "+-----BEGIN RSA PRIVATE KEY-----"),
        ("cadena de conexión", "+DB = postgres://juan:secreta@servidor/base"),
    ],
)
def test_reconoce_cada_tipo(nombre: str, linea: str) -> None:
    hallazgos = historial._buscar(f"commit aaaaaaaa\n{linea}\n")

    assert [h["tipo"] for h in hallazgos] == [nombre]


def test_sin_git_lo_dice(tmp_path: Path) -> None:
    salida = historial.revisar(tmp_path)

    assert "no es un repositorio git" in salida["nota"]


def test_se_dice_hasta_donde_se_miro(tmp_path: Path) -> None:
    """Un resultado parcial presentado como completo engaña."""
    (tmp_path / ".git").mkdir()

    with mock.patch.object(historial, "_historial", return_value=HISTORIA):
        salida = historial.revisar(tmp_path, commits=50)

    assert "50 commits" in salida["nota"]


def test_el_resumen_dice_que_hay_que_rotarlas() -> None:
    """Borrar el archivo no basta, y esa es toda la diferencia."""
    dicho = historial.resumen(
        {"revisados": 100, "hallazgos": historial._buscar(HISTORIA)}
    )

    assert "rotarlos" in dicho
    assert "siguen en los commits" in dicho


def test_sin_hallazgos_tambien_se_dice_cuanto_se_miro() -> None:
    dicho = historial.resumen({"revisados": 100, "hallazgos": []})

    assert "100" in dicho


# =========================================================
# Competencias declaradas
# =========================================================


def test_los_agentes_declaran_lo_que_saben() -> None:
    """`capabilities()` existía y todos devolvían una lista vacía."""
    from ai_architect.commands import experto

    declaradas = experto.del_proyecto()

    assert len(declaradas) >= 10
    assert "seguridad" in declaradas
    assert "dependencias" in declaradas


def test_se_les_llama_por_su_nombre_corto() -> None:
    """ "El de rendimiento", no "Pandas Iteration Detection"."""
    from ai_architect.commands import experto

    declaradas = experto.del_proyecto()

    for nombre in ("rendimiento", "pruebas", "arquitectura", "documentacion"):
        assert nombre in declaradas


def test_sin_agentes_queda_el_respaldo() -> None:
    """Perder el reparto porque un agente no rellenó su ficha sería peor."""
    from ai_architect.commands import experto

    with mock.patch(
        "ai_architect.agents.agent_manager.AgentManager", side_effect=RuntimeError("x")
    ):
        assert experto.del_proyecto() == experto.POR_DEFECTO_PROYECTO


def test_el_agente_de_dependencias_devuelve_vulnerabilidades(tmp_path: Path) -> None:
    from ai_architect.agents.dependency_agent import DependencyAgent

    (tmp_path / "requirements.txt").write_text("gitpython>=3.1.43\n")

    with mock.patch.object(
        cve,
        "revisar",
        return_value={
            "vulnerables": [
                {"paquete": "gitpython", "version": "3.1.43", "fallos": ["GHSA-x"]}
            ],
            "detalle": [],
            "nota": "x",
        },
    ):
        salida = DependencyAgent().review(str(tmp_path))

    assert salida["vulnerabilities"]
    assert "gitpython" in salida["findings"][0]


def test_el_agente_de_seguridad_mira_el_historial(tmp_path: Path) -> None:
    from ai_architect.agents.security_agent import SecurityAgent

    with mock.patch.object(
        historial,
        "revisar",
        return_value={
            "revisados": 100,
            "hallazgos": [
                {"tipo": "clave de OpenAI", "commit": "abc12345", "muestra": "«oculto»"}
            ],
            "nota": "x",
        },
    ):
        salida = SecurityAgent().review(str(tmp_path))

    commiteados = [f for f in salida["findings"] if "historial" in f["file"]]

    assert commiteados
    assert commiteados[0]["severity"] == "CRITICAL"


def test_un_secreto_commiteado_pesa_mas_que_uno_en_disco(tmp_path: Path) -> None:
    """Borrar el archivo lo arregla; el del historial hay que rotarlo."""
    from ai_architect.agents.security_agent import SecurityAgent

    limpio = {"revisados": 100, "hallazgos": [], "nota": ""}

    sucio = {
        "revisados": 100,
        "hallazgos": [{"tipo": "clave de OpenAI", "commit": "a", "muestra": "x"}],
        "nota": "",
    }

    with mock.patch.object(historial, "revisar", return_value=limpio):
        bien = SecurityAgent().review(str(tmp_path))["security_score"]

    with mock.patch.object(historial, "revisar", return_value=sucio):
        mal = SecurityAgent().review(str(tmp_path))["security_score"]

    assert mal < bien
