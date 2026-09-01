"""Los cuatro agentes que se rescataron del montón de huérfanos.

De los diecinueve agentes que nadie construía, doce **ni siquiera se podían
instanciar**: heredaban de ``BaseAgent``, que declara ``run`` abstracto, y
ninguno lo implementaba. Cualquier intento de usarlos moría en
``TypeError``.

Estos cuatro se arreglaron y se conectaron porque aportan señal que los
siete de antes no daban. Los demás se podaron.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect.agents.bug_hunter_agent import BugHunterAgent
from ai_architect.agents.devops_agent import DevOpsAgent
from ai_architect.agents.performance_agent import PerformanceAgent
from ai_architect.agents.release_agent import ReleaseAgent


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")
    return tmp_path


# --- Se pueden instanciar ---------------------------------------------------


@pytest.mark.parametrize(
    "clase",
    [BugHunterAgent, PerformanceAgent, DevOpsAgent, ReleaseAgent],
)
def test_se_pueden_construir(clase: type) -> None:
    """La regresión: ``TypeError: Can't instantiate abstract class``."""
    assert clase() is not None


@pytest.mark.parametrize(
    "clase",
    [BugHunterAgent, PerformanceAgent, DevOpsAgent, ReleaseAgent],
)
def test_run_delega_en_review(clase: type, proyecto: Path) -> None:
    agente = clase()

    assert agente.run(str(proyecto)) == agente.review(str(proyecto))


# --- Bug Hunter -------------------------------------------------------------


def test_encuentra_el_except_pelado(proyecto: Path) -> None:
    (proyecto / "malo.py").write_text(
        "try:\n    x = 1\nexcept:\n    x = 2\n",
        encoding="utf-8",
    )

    tipos = [f["type"] for f in BugHunterAgent().review(str(proyecto))["findings"]]

    assert "bare_except" in tipos


def test_encuentra_el_except_que_se_traga_el_error(proyecto: Path) -> None:
    (proyecto / "malo.py").write_text(
        "try:\n    x = 1\nexcept ValueError:\n    pass\n",
        encoding="utf-8",
    )

    hallazgos = BugHunterAgent().review(str(proyecto))["findings"]

    assert hallazgos[0]["type"] == "silent_except"
    assert hallazgos[0]["line"] == 3


def test_encuentra_los_marcadores_pendientes(proyecto: Path) -> None:
    (proyecto / "malo.py").write_text("# TODO: arreglar esto\n", encoding="utf-8")

    tipos = [f["type"] for f in BugHunterAgent().review(str(proyecto))["findings"]]

    assert tipos == ["marker"]


def test_encuentra_el_argumento_mutable_por_defecto(proyecto: Path) -> None:
    (proyecto / "malo.py").write_text("def f(x=[]):\n    return x\n", encoding="utf-8")

    tipos = [f["type"] for f in BugHunterAgent().review(str(proyecto))["findings"]]

    assert "mutable_default" in tipos


def test_pass_dentro_de_password_ya_no_cuenta(proyecto: Path) -> None:
    """La regresión: buscaba subcadenas sobre el archivo en minúsculas, así
    que ``"pass"`` saltaba con "password", "passed" y "passing", y ``"todo"``
    con "todos". Todos los archivos casaban con todos los patrones."""
    (proyecto / "bueno.py").write_text(
        'password = leer()\nresultado = "passed"\ntodos = []\n',
        encoding="utf-8",
    )

    assert BugHunterAgent().review(str(proyecto))["total"] == 0


def test_un_archivo_limpio_no_genera_nada(proyecto: Path) -> None:
    assert BugHunterAgent().review(str(proyecto))["total"] == 0


def test_el_hallazgo_dice_archivo_y_linea(proyecto: Path) -> None:
    (proyecto / "malo.py").write_text("\n\n# FIXME: ya\n", encoding="utf-8")

    hallazgo = BugHunterAgent().review(str(proyecto))["findings"][0]

    assert hallazgo["line"] == 3
    assert hallazgo["file"].endswith("malo.py")


def test_no_mira_dentro_del_venv(proyecto: Path) -> None:
    paquete = proyecto / ".venv" / "Lib"
    paquete.mkdir(parents=True)
    (paquete / "ajeno.py").write_text("try:\n    x=1\nexcept:\n    x=2\n", "utf-8")

    assert BugHunterAgent().review(str(proyecto))["total"] == 0


# --- Performance ------------------------------------------------------------


def test_encuentra_iterrows(proyecto: Path) -> None:
    (proyecto / "lento.py").write_text(
        "for i, fila in df.iterrows():\n    pass\n",
        encoding="utf-8",
    )

    tipos = [f["type"] for f in PerformanceAgent().review(str(proyecto))["findings"]]

    assert "iterrows" in tipos


def test_encuentra_range_len(proyecto: Path) -> None:
    (proyecto / "lento.py").write_text(
        "for i in range(len(datos)):\n    print(i)\n",
        encoding="utf-8",
    )

    tipos = [f["type"] for f in PerformanceAgent().review(str(proyecto))["findings"]]

    assert "range_len" in tipos


def test_un_bucle_normal_no_es_un_hallazgo(proyecto: Path) -> None:
    (proyecto / "bien.py").write_text(
        "for i, x in enumerate(datos):\n    pass\n",
        encoding="utf-8",
    )

    assert PerformanceAgent().review(str(proyecto))["total"] == 0


# --- DevOps -----------------------------------------------------------------


def test_detecta_que_no_hay_ci(proyecto: Path) -> None:
    informe = DevOpsAgent().review(str(proyecto))

    assert informe["continuous_integration"] is False
    assert [f["type"] for f in informe["findings"]] == ["sin_ci", "sin_pyproject"]


def test_una_carpeta_de_flujos_vacia_no_es_ci(proyecto: Path) -> None:
    """``.github/workflows`` sin un solo ``.yml`` dentro no ejecuta nada."""
    (proyecto / ".github" / "workflows").mkdir(parents=True)

    assert DevOpsAgent().review(str(proyecto))["continuous_integration"] is False


def test_con_ci_y_pyproject_no_hay_nada_que_decir(proyecto: Path) -> None:
    flujos = proyecto / ".github" / "workflows"
    flujos.mkdir(parents=True)
    (flujos / "ci.yml").write_text("on: push\n", encoding="utf-8")
    (proyecto / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    assert DevOpsAgent().review(str(proyecto))["findings"] == []


def test_detecta_el_dockerfile(proyecto: Path) -> None:
    (proyecto / "Dockerfile").write_text("FROM python\n", encoding="utf-8")

    assert DevOpsAgent().review(str(proyecto))["docker"] is True


# --- Release ----------------------------------------------------------------


def test_avisa_de_que_falta_el_changelog(proyecto: Path) -> None:
    informe = ReleaseAgent().review(str(proyecto))

    assert informe["changelog"] is False
    assert informe["release_ready"] is False


def test_la_version_del_pyproject_cuenta(proyecto: Path) -> None:
    """No todo proyecto guarda un archivo VERSION."""
    (proyecto / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    assert ReleaseAgent().review(str(proyecto))["version"] is True


def test_con_changelog_y_version_esta_listo(proyecto: Path) -> None:
    (proyecto / "CHANGELOG.md").write_text("# 1.0\n", encoding="utf-8")
    (proyecto / "VERSION").write_text("1.0\n", encoding="utf-8")

    informe = ReleaseAgent().review(str(proyecto))

    assert informe["release_ready"] is True
    assert informe["findings"] == []
