"""Los agentes obedecen: Architect ordena y ellos ejecutan de verdad. Aquí las
herramientas externas se doblan (conftest) y cada prueba las vuelve a doblar
para ver qué orden se lanzó."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect.agente import caja
from ai_architect.agente.herramientas import equipo
from ai_architect.agents import ordenes
from ai_architect.commands import pendientes


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "1.2.3"\n', encoding="utf-8"
    )
    (tmp_path / "instalador.iss").write_text(
        '#define Version    "1.2.3"\n', encoding="utf-8"
    )
    (tmp_path / "ai_architect").mkdir()
    (tmp_path / "ai_architect" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    return tmp_path


@pytest.fixture
def lanzadas(monkeypatch) -> list[list[str]]:
    """Registra cada orden que un agente lanza y contesta que salió bien."""
    vistas: list[list[str]] = []

    def correr_falso(orden, cwd, timeout=120):
        vistas.append([str(p) for p in orden])
        return 0, "1 passed in 0.1s\n", ""

    monkeypatch.setattr(ordenes, "correr", correr_falso)
    monkeypatch.setattr(ordenes, "modulo_disponible", lambda raiz, m: True)
    monkeypatch.setattr(ordenes, "hay", lambda p: True)
    return vistas


# --- el catálogo -------------------------------------------------------------------


def test_cada_agente_tiene_tareas_con_nombre_y_marca_de_cambio() -> None:
    for clave, tareas in ordenes.CATALOGO.items():
        assert clave in equipo.EQUIPO, clave
        for nombre, tarea in tareas.items():
            assert tarea.nombre == nombre and tarea.que and callable(tarea.hacer)


def test_una_tarea_desconocida_dice_cuales_hay(repo: Path) -> None:
    salida = ordenes.ejecutar("git", "volar", str(repo))

    assert salida["ok"] is False and "commit" in salida["hecho"]


def test_un_agente_sin_tareas_lo_dice(repo: Path) -> None:
    salida = ordenes.ejecutar("metricas", "algo", str(repo))

    assert salida["ok"] is False and "ninguna" in salida["hecho"]


# --- calidad y errores --------------------------------------------------------------


def test_formatear_lanza_black_sobre_el_paquete_y_las_pruebas(
    repo: Path, lanzadas
) -> None:
    salida = ordenes.ejecutar("calidad", "formatear", str(repo))

    assert salida["ok"]
    assert lanzadas[-1][1:5] == ["-m", "black", "-q", "ai_architect"]
    assert lanzadas[-1][-1] == "tests"


def test_corregir_errores_limita_a_los_reales(repo: Path, lanzadas) -> None:
    ordenes.ejecutar("errores", "corregir", str(repo))

    assert "--fix" in lanzadas[-1] and "F,B,PLE" in lanzadas[-1]


def test_sin_black_no_revienta(repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(ordenes, "modulo_disponible", lambda raiz, m: False)

    salida = ordenes.ejecutar("calidad", "formatear", str(repo))

    assert salida["ok"] is False and "black" in salida["hecho"]


# --- git ---------------------------------------------------------------------------------


def test_commit_hace_add_y_commit(repo: Path, lanzadas) -> None:
    salida = ordenes.ejecutar("git", "commit", str(repo), mensaje="Arreglo la voz")

    assert salida["ok"]
    assert lanzadas[0][:3] == ["git", "add", "-A"]
    assert (
        lanzadas[1][:3] == ["git", "commit", "-q"] and "Arreglo la voz" in lanzadas[1]
    )


def test_commit_sin_mensaje_no_hace_nada(repo: Path, lanzadas) -> None:
    salida = ordenes.ejecutar("git", "commit", str(repo))

    assert salida["ok"] is False and not lanzadas


def test_subir_y_traer(repo: Path, lanzadas) -> None:
    assert ordenes.ejecutar("git", "subir", str(repo))["ok"]
    assert ordenes.ejecutar("git", "traer", str(repo))["ok"]
    assert lanzadas[0][:2] == ["git", "push"]
    assert lanzadas[1][:3] == ["git", "pull", "--ff-only"]


def test_rama_rechaza_nombres_raros(repo: Path, lanzadas) -> None:
    assert ordenes.ejecutar("git", "rama", str(repo), nombre="mala rama")["ok"] is False
    assert ordenes.ejecutar("git", "rama", str(repo), nombre="voz/eco")["ok"]


# --- publicación -------------------------------------------------------------------------


def test_anotar_changelog_crea_la_seccion_con_los_commits(
    repo: Path, monkeypatch
) -> None:
    def git_falso(orden, cwd, timeout=120):
        if "describe" in orden:
            return 0, "v1.2.2\n", ""
        if "log" in orden:
            return 0, "Arreglo el eco\nDictado a Word\n", ""
        return 0, "", ""

    monkeypatch.setattr(ordenes, "correr", git_falso)
    (repo / "CHANGELOG.md").write_text(
        "# Cambios\n\n## 1.2.2\n- algo\n", encoding="utf-8"
    )

    salida = ordenes.ejecutar("publicacion", "anotar_changelog", str(repo))

    texto = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert salida["ok"]
    assert texto.index("## 1.2.3") < texto.index("## 1.2.2")
    assert "- Arreglo el eco" in texto and "- Dictado a Word" in texto


def test_anotar_changelog_no_repite_la_version(repo: Path, lanzadas) -> None:
    (repo / "CHANGELOG.md").write_text("## 1.2.3\n- ya\n", encoding="utf-8")

    salida = ordenes.ejecutar("publicacion", "anotar_changelog", str(repo))

    assert salida["ok"] and "ya tiene" in salida["hecho"]


def test_subir_version_cambia_pyproject_e_instalador(repo: Path) -> None:
    salida = ordenes.ejecutar(
        "publicacion", "subir_version", str(repo), version="1.3.0"
    )

    assert salida["ok"]
    assert 'version = "1.3.0"' in (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert '"1.3.0"' in (repo / "instalador.iss").read_text(encoding="utf-8")


def test_subir_version_exige_x_y_z(repo: Path) -> None:
    assert (
        ordenes.ejecutar("publicacion", "subir_version", str(repo), version="v2")["ok"]
        is False
    )


# --- empaquetado, pruebas, devops, seguridad ------------------------------------------------


def test_etiquetar_usa_la_version_del_proyecto(repo: Path, lanzadas) -> None:
    salida = ordenes.ejecutar("empaquetado", "etiquetar", str(repo))

    assert salida["ok"] and "v1.2.3" in salida["hecho"]
    assert lanzadas[0][:3] == ["git", "tag", "-a"] and "v1.2.3" in lanzadas[0]
    assert lanzadas[1][:2] == ["git", "push"] and "v1.2.3" in lanzadas[1]


def test_reconstruir_delega_en_la_autoreparacion(repo: Path, monkeypatch) -> None:
    from ai_architect import autoreparacion

    monkeypatch.setattr(
        autoreparacion,
        "reconstruir",
        lambda averia=None: {
            "ok": True,
            "informe": "Instalador reconstruido",
            "instalador": "x",
        },
    )

    salida = ordenes.ejecutar("empaquetado", "reconstruir", str(repo))

    assert salida["ok"] and "reconstruido" in salida["hecho"]


def test_correr_pruebas_devuelve_el_resumen(repo: Path, lanzadas) -> None:
    salida = ordenes.ejecutar(
        "pruebas", "correr", str(repo), ruta="tests/voz", filtro="eco"
    )

    assert salida["ok"] and salida["resumen"] == "1 passed in 0.1s"
    assert "tests/voz" in lanzadas[-1] and lanzadas[-1][-2:] == ["-k", "eco"]


def test_relanzar_ci_busca_la_ultima_fallida(repo: Path, monkeypatch, lanzadas) -> None:
    monkeypatch.setattr(
        ordenes,
        "correr_json",
        lambda orden, cwd, timeout=120: [
            {"databaseId": 7, "conclusion": "success", "displayTitle": "a"},
            {"databaseId": 5, "conclusion": "failure", "displayTitle": "b"},
        ],
    )

    salida = ordenes.ejecutar("devops", "relanzar_ci", str(repo))

    assert salida["ok"] and "5" in salida["hecho"]
    assert lanzadas[-1][:4] == ["gh", "run", "rerun", "5"]


def test_ver_ci_sin_gh_lo_dice(repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(ordenes, "hay", lambda p: False)

    assert "gh" in ordenes.ejecutar("devops", "ver_ci", str(repo))["hecho"]


def test_proteger_secretos_completa_el_gitignore(repo: Path) -> None:
    (repo / ".gitignore").write_text(".venv/\n.env\n", encoding="utf-8")

    salida = ordenes.ejecutar("seguridad", "proteger_secretos", str(repo))

    texto = (repo / ".gitignore").read_text(encoding="utf-8")
    assert salida["ok"] and ".env.*" in texto and "*.key" in texto
    assert texto.splitlines().count(".env") == 1
    assert (
        "ya protege"
        in ordenes.ejecutar("seguridad", "proteger_secretos", str(repo))["hecho"]
    )


def test_instalar_paquete_pasa_por_instalar(repo: Path, monkeypatch) -> None:
    from ai_architect import instalar

    vistos: list[str] = []
    monkeypatch.setattr(
        instalar,
        "paquete",
        lambda nombre, req=None: vistos.append(nombre)
        or {"ok": True, "requirements": True},
    )

    salida = ordenes.ejecutar("dependencias", "instalar", str(repo), paquete="rich")

    assert salida["ok"] and vistos == ["rich"] and salida["requirements"] is True


def test_actualizar_todos_usa_la_lista_de_desactualizados(
    repo: Path, monkeypatch, lanzadas
) -> None:
    monkeypatch.setattr(
        ordenes,
        "correr_json",
        lambda orden, cwd, timeout=120: [{"name": "rich"}, {"name": "httpx"}],
    )

    salida = ordenes.ejecutar("dependencias", "actualizar", str(repo))

    assert salida["ok"] and "rich" in salida["hecho"]
    assert lanzadas[-1][-2:] == ["rich", "httpx"] and "--upgrade" in lanzadas[-1]


def test_una_tarea_que_revienta_se_cuenta(repo: Path, monkeypatch) -> None:
    def explota(raiz, args):
        raise RuntimeError("sin red")

    monkeypatch.setitem(
        ordenes.CATALOGO["git"], "commit", ordenes.Tarea("commit", "x", explota)
    )

    salida = ordenes.ejecutar("git", "commit", str(repo), mensaje="m")

    assert salida["ok"] is False and "sin red" in salida["hecho"]


# --- como herramientas de Architect -----------------------------------------------------


def test_ordenar_esta_en_la_caja_y_pide_permiso(tmp_path: Path) -> None:
    nombres = caja.nombres(caja.herramientas_para(tmp_path))

    assert "ordenar" in nombres and "consultar" in nombres
    assert "ordenar" in caja.ESCRIBEN and "consultar" not in caja.ESCRIBEN


def test_ordenar_manda_al_agente(repo: Path, lanzadas) -> None:
    resultado = equipo.OrdenarTool(str(repo)).execute(
        agente="git", tarea="commit", argumentos={"mensaje": "hola"}
    )

    assert resultado.success and "git.commit" in resultado.content
    assert lanzadas[1][:2] == ["git", "commit"]


def test_ordenar_no_acepta_tareas_de_consulta_y_viceversa(repo: Path, lanzadas) -> None:
    mal = equipo.OrdenarTool(str(repo)).execute(agente="pruebas", tarea="correr")
    assert not mal.success and "consultar" in mal.content

    mal = equipo.ConsultarTool(str(repo)).execute(agente="git", tarea="subir")
    assert not mal.success and "ordenar" in mal.content

    bien = equipo.ConsultarTool(str(repo)).execute(agente="pruebas", tarea="correr")
    assert bien.success and "passed" in bien.content


def test_la_descripcion_de_ordenar_lista_las_tareas(repo: Path) -> None:
    spec = equipo.OrdenarTool(str(repo)).spec

    assert "git: commit" in spec.description and "reconstruir" in spec.description
    assert "correr" not in spec.description.split("pruebas:")[-1][:5]
    assert set(spec.parameters["properties"]["agente"]["enum"]) >= {"git", "calidad"}


def test_la_cola_describe_la_orden() -> None:
    texto = pendientes._describir(
        "ordenar", {"agente": "git", "tarea": "subir", "argumentos": {}}
    )

    assert texto.startswith("ordenar a git: subir")


def test_el_guion_dice_que_los_agentes_obedecen(tmp_path: Path) -> None:
    from ai_architect.agente.guion import prompt_sistema

    texto = prompt_sistema(tmp_path, "Efraín", False)

    assert "`ordenar`" in texto and "`consultar`" in texto and "OBEDECEN" in texto
