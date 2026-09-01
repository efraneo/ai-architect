"""`changelog/` sabía guardar y escribir, pero nadie construía las entradas.

Faltaba la pieza que mira el repositorio y dice qué ha cambiado. Y el
escritor tenía un fallo de fondo: ``write()`` hacía ``write_text`` con una
sola entrada, así que **llamarlo dos veces dejaba solo la última**. Un
changelog que olvida lo anterior no es un changelog.

Mientras tanto, el `ReleaseAgent` reportaba en cada inspección: "no hay
CHANGELOG: nadie sabe qué cambió entre versiones".
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ai_architect.changelog.changelog_builder import (
    ChangeLogBuilder,
    clasificar,
    resumir,
)
from ai_architect.changelog.changelog_writer import ChangeLogWriter
from ai_architect.changelog.models import ChangeItem, ChangeLogEntry, ChangeType
from ai_architect.commands import changelog


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
    git(tmp_path, "commit", "-m", "feat: primer módulo")

    return tmp_path


def entrada(version: str = "1.0.0", cambios: list[ChangeItem] | None = None):
    e = ChangeLogEntry(version=version, author="Prueba")

    for item in cambios or []:
        e.add(item)

    return e


# --- Clasificar el commit ---------------------------------------------------


@pytest.mark.parametrize(
    ("asunto", "esperado"),
    [
        ("fix: arregla el parser", ChangeType.FIX),
        ("fix(agents): arregla el parser", ChangeType.FIX),
        ("fix!: cambio incompatible", ChangeType.FIX),
        ("feat: agentes nuevos", ChangeType.CREATE),
        ("refactor: extrae el validador", ChangeType.REFACTOR),
        ("remove: quita el paquete llm", ChangeType.DELETE),
    ],
)
def test_reconoce_el_prefijo(asunto: str, esperado: ChangeType) -> None:
    assert clasificar(asunto) == esperado


def test_lo_que_no_se_reconoce_es_update() -> None:
    """Inventarles categoría a los commits normales sería peor."""
    assert clasificar("Conectar swarm y autonomous") == ChangeType.UPDATE


def test_un_asunto_vacio_no_revienta() -> None:
    assert clasificar("") == ChangeType.UPDATE


# --- Resumir los archivos ---------------------------------------------------


def test_un_archivo_se_nombra() -> None:
    assert resumir(["ai_architect/cli.py"]) == "ai_architect/cli.py"


def test_varios_de_la_misma_carpeta_se_cuentan_con_su_carpeta() -> None:
    """"12 archivos en agents" orienta más que doce rutas seguidas."""
    rutas = [f"ai_architect/agents/a{i}.py" for i in range(3)]

    assert resumir(rutas) == "3 archivos en ai_architect/agents"


def test_de_carpetas_distintas_solo_se_cuentan() -> None:
    assert resumir(["a/uno.py", "b/dos.py"]) == "2 archivos"


def test_sin_archivos_no_hay_resumen() -> None:
    assert resumir([]) == ""


# --- El escritor no borra lo anterior ---------------------------------------


def test_escribe_la_primera_version(tmp_path: Path) -> None:
    destino = tmp_path / "CHANGELOG.md"

    ChangeLogWriter().write(entrada("1.0.0"), destino)

    assert "# ChangeLog" in destino.read_text(encoding="utf-8")
    assert "## 1.0.0" in destino.read_text(encoding="utf-8")


def test_la_segunda_version_no_borra_la_primera(tmp_path: Path) -> None:
    """La regresión: ``write_text`` dejaba solo la última entrada."""
    destino = tmp_path / "CHANGELOG.md"
    escritor = ChangeLogWriter()

    escritor.write(entrada("1.0.0"), destino)
    escritor.write(entrada("2.0.0"), destino)

    contenido = destino.read_text(encoding="utf-8")

    assert "## 1.0.0" in contenido
    assert "## 2.0.0" in contenido


def test_lo_nuevo_va_arriba(tmp_path: Path) -> None:
    """Quien abre un CHANGELOG quiere la última versión, no la primera."""
    destino = tmp_path / "CHANGELOG.md"
    escritor = ChangeLogWriter()

    escritor.write(entrada("1.0.0"), destino)
    escritor.write(entrada("2.0.0"), destino)

    contenido = destino.read_text(encoding="utf-8")

    assert contenido.index("## 2.0.0") < contenido.index("## 1.0.0")


def test_la_cabecera_no_se_duplica(tmp_path: Path) -> None:
    destino = tmp_path / "CHANGELOG.md"
    escritor = ChangeLogWriter()

    escritor.write(entrada("1.0.0"), destino)
    escritor.write(entrada("2.0.0"), destino)

    assert destino.read_text(encoding="utf-8").count("# ChangeLog") == 1


def test_respeta_un_changelog_escrito_a_mano(tmp_path: Path) -> None:
    destino = tmp_path / "CHANGELOG.md"
    destino.write_text("# ChangeLog\n\n## 0.1.0\n\nLo de antes.\n", encoding="utf-8")

    ChangeLogWriter().write(entrada("1.0.0"), destino)

    contenido = destino.read_text(encoding="utf-8")

    assert "Lo de antes." in contenido
    assert "## 1.0.0" in contenido


def test_el_bloque_lleva_las_lineas_movidas() -> None:
    item = ChangeItem(
        file="modulo.py",
        change_type=ChangeType.FIX,
        summary="arregla algo",
        additions=10,
        deletions=3,
    )

    bloque = ChangeLogWriter().render(entrada("1.0.0", [item]))

    assert "(+10/-3)" in bloque
    assert "arregla algo" in bloque


def test_una_version_sin_cambios_lo_dice() -> None:
    assert "Sin cambios" in ChangeLogWriter().render(entrada("1.0.0"))


# --- El constructor, contra un repositorio de verdad ------------------------


def test_construye_desde_los_commits(repo: Path) -> None:
    entrada_construida = ChangeLogBuilder(repo).build(version="1.0.0")

    assert entrada_construida.total_changes == 1
    assert entrada_construida.changes[0].summary == "feat: primer módulo"
    assert entrada_construida.changes[0].change_type == ChangeType.CREATE


def test_un_item_por_commit_no_por_archivo(repo: Path) -> None:
    """La primera versión sacaba 643 líneas sobre este repositorio: una por
    archivo y commit, casi todas repitiendo el mismo asunto."""
    for i in range(3):
        (repo / f"otro{i}.py").write_text(f"x = {i}\n", encoding="utf-8")

    git(repo, "add", ".")
    git(repo, "commit", "-m", "feat: tres de golpe")

    construida = ChangeLogBuilder(repo).build()

    assert construida.total_changes == 2
    assert "3 archivos" in construida.changes[0].file


def test_cuenta_desde_la_ultima_etiqueta(repo: Path) -> None:
    git(repo, "tag", "v1.0.0")

    (repo / "nuevo.py").write_text("y = 2\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fix: después de la etiqueta")

    construida = ChangeLogBuilder(repo).build()

    assert construida.total_changes == 1
    assert construida.changes[0].summary == "fix: después de la etiqueta"


def test_sin_etiquetas_cuenta_todo(repo: Path) -> None:
    assert ChangeLogBuilder(repo).desde_la_ultima_etiqueta() == ""


# --- El comando -------------------------------------------------------------


def test_por_defecto_no_escribe_nada(repo: Path) -> None:
    """Modificar un archivo del repositorio por ejecutar un comando es una
    sorpresa desagradable."""
    resultado = changelog.run(str(repo), version="1.0.0")

    assert resultado["success"] is True
    assert resultado["written"] is False
    assert not (repo / "CHANGELOG.md").exists()


def test_con_write_si_escribe(repo: Path) -> None:
    resultado = changelog.run(str(repo), version="1.0.0", write=True)

    assert resultado["written"] is True
    assert "## 1.0.0" in (repo / "CHANGELOG.md").read_text(encoding="utf-8")


def test_el_resultado_resume_por_tipo(repo: Path) -> None:
    resultado = changelog.run(str(repo), version="1.0.0")

    assert resultado["total_changes"] == 1
    assert resultado["by_type"] == {"CREATE": 1}


def test_una_carpeta_que_no_es_repositorio(tmp_path: Path) -> None:
    resultado = changelog.run(str(tmp_path))

    assert resultado["success"] is False
    assert resultado["error"] == "Not a git repository."


def test_un_repositorio_inexistente(tmp_path: Path) -> None:
    resultado = changelog.run(str(tmp_path / "no-existe"))

    assert resultado["success"] is False
    assert resultado["error"] == "Repository not found."
