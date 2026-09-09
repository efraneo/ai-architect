"""La biblioteca de especialistas, habilidades y reglas: instalar desde una
carpeta, buscar por tema, usar una habilidad, delegar en un especialista."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_architect import biblioteca
from ai_architect.agente.herramientas import biblioteca as herramientas
from ai_architect.commands import biblioteca as por_voz_


@pytest.fixture
def fuente(tmp_path: Path) -> Path:
    raiz = tmp_path / "fuente"
    (raiz / "agents").mkdir(parents=True)
    (raiz / "agents" / "security-reviewer.md").write_text(
        "---\nname: security-reviewer\ndescription: Security vulnerability detection. "
        "Flags secrets, SSRF, injection.\ntools: Read, Grep, Glob, Bash\nmodel: sonnet\n---\n"
        "You are a security reviewer.\n",
        encoding="utf-8",
    )
    (raiz / "agents" / "python-reviewer.md").write_text(
        "---\nname: python-reviewer\ndescription: Python code review\ntools: Read\n---\nReview Python.\n",
        encoding="utf-8",
    )
    (raiz / "skills" / "django-security").mkdir(parents=True)
    (raiz / "skills" / "django-security" / "SKILL.md").write_text(
        "---\nname: django-security\ndescription: Django security best practices\n---\n# Django security\n\n1. CSRF\n2. ORM\n",
        encoding="utf-8",
    )
    (raiz / "skills" / "django-security" / "references").mkdir()
    (raiz / "skills" / "django-security" / "references" / "owasp.md").write_text(
        "OWASP top 10 for Django", encoding="utf-8"
    )
    (raiz / "skills" / "django-security" / "run.sh").write_text(
        "echo no", encoding="utf-8"
    )
    (raiz / "skills" / "tdd-workflow").mkdir()
    (raiz / "skills" / "tdd-workflow" / "SKILL.md").write_text(
        "---\nname: tdd-workflow\ndescription: Test driven development workflow\n---\nRED GREEN REFACTOR\n",
        encoding="utf-8",
    )
    (raiz / "rules" / "common").mkdir(parents=True)
    (raiz / "rules" / "common" / "security.md").write_text(
        "# Security rules\n\nNever log secrets.\n", encoding="utf-8"
    )
    (raiz / "rules" / "python").mkdir()
    (raiz / "rules" / "python" / "style.md").write_text(
        "# Python style\n\nUse ruff.\n", encoding="utf-8"
    )
    (raiz / "commands").mkdir()
    (raiz / "commands" / "quality-gate.md").write_text(
        "---\ndescription: Verification gate before merging\n---\nRun all checks.\n",
        encoding="utf-8",
    )
    return raiz


@pytest.fixture
def instalada(fuente: Path) -> dict:
    salida = biblioteca.instalar(str(fuente))
    assert salida["ok"], salida
    return salida


def test_instalar_desde_carpeta_copia_solo_contenido(instalada, fuente: Path) -> None:
    assert biblioteca.instalada()
    assert (
        instalada["agents"] == 2
        and instalada["skills"] == 3
        and instalada["rules"] == 2
    )
    assert not (biblioteca.ruta() / "skills" / "django-security" / "run.sh").exists()
    assert biblioteca.cuenta() == {
        "especialistas": 2,
        "habilidades": 2,
        "reglas": 2,
        "recetas": 1,
    }


def test_buscar_por_tema_con_sinonimos(instalada) -> None:
    nombres = [e["nombre"] for e in biblioteca.buscar("seguridad django")]

    assert nombres[0] == "django-security"
    assert "security-reviewer" in nombres and "common/security" in nombres
    assert (
        biblioteca.buscar("seguridad", "especialistas")[0]["nombre"]
        == "security-reviewer"
    )
    assert biblioteca.buscar("pruebas")[0]["nombre"] == "tdd-workflow"
    assert biblioteca.buscar("") == []


def test_habilidad_y_anexo(instalada) -> None:
    h = biblioteca.habilidad("django security")

    assert (
        h is not None
        and "CSRF" in h["contenido"]
        and h["anexos"] == ["references\\owasp.md"]
        or (h is not None and h["anexos"] == ["references/owasp.md"])
    )
    assert "OWASP" in biblioteca.anexo("django-security", h["anexos"][0])
    assert biblioteca.anexo("django-security", "../../agents/python-reviewer.md") == ""
    assert biblioteca.habilidad("no-existe") is None


def test_especialista_y_reglas(instalada, tmp_path: Path) -> None:
    e = biblioteca.especialista("security-reviewer")

    assert e is not None and e["herramientas"] == ["Read", "Grep", "Glob", "Bash"]
    assert e["modelo"] == "sonnet" and "security reviewer" in e["guion"]
    assert [r["nombre"] for r in biblioteca.reglas("python")] == ["python/style"]
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    assert biblioteca.reglas_para(tmp_path) == ["common", "python"]


def test_sin_instalar_no_hay_nada(tmp_path: Path) -> None:
    assert biblioteca.instalada() is False
    assert biblioteca.buscar("seguridad") == []
    assert "no existe" in biblioteca.instalar(str(tmp_path / "nada"))["error"]


def test_instalar_desde_github_baja_el_zip(monkeypatch, tmp_path: Path) -> None:
    import io
    import zipfile

    memoria = io.BytesIO()

    with zipfile.ZipFile(memoria, "w") as z:
        z.writestr(
            "ECC-main/agents/planner.md",
            "---\nname: planner\ndescription: plans\n---\nPlan.\n",
        )
        z.writestr(
            "ECC-main/skills/x/SKILL.md", "---\nname: x\ndescription: y\n---\nz\n"
        )
        z.writestr("ECC-main/scripts/evil.js", "nope")

    class Respuesta:
        status_code = 200
        content = memoria.getvalue()

    import requests

    monkeypatch.setattr(requests, "get", lambda url, timeout=0: Respuesta())

    salida = biblioteca.instalar("https://github.com/alguien/ECC")

    assert salida["ok"] and salida["agents"] == 1 and salida["skills"] == 1
    assert not list(biblioteca.ruta().glob("**/*.js"))
    assert biblioteca.estado()["origen"] == "https://github.com/alguien/ECC"


# --- las herramientas -------------------------------------------------------------------


def test_buscar_y_usar_habilidad_como_herramientas(instalada) -> None:
    r = herramientas.BuscarHabilidadTool().execute(tema="seguridad en django")
    assert r.success and "django-security" in r.content

    r = herramientas.UsarHabilidadTool().execute(nombre="django-security")
    assert r.success and "CSRF" in r.content and "Anexos" in r.content

    r = herramientas.UsarHabilidadTool().execute(nombre="django-sec")
    assert not r.success and "django-security" in r.content

    r = herramientas.AnexoHabilidadTool().execute(
        nombre="django-security", archivo="references/owasp.md"
    )
    assert r.success and "OWASP" in r.content


def test_sin_biblioteca_la_herramienta_lo_dice() -> None:
    r = herramientas.BuscarHabilidadTool().execute(tema="seguridad")

    assert not r.success and "instalar" in r.content


def test_el_especialista_corre_aparte_con_su_guion(
    instalada, tmp_path: Path, monkeypatch
) -> None:
    visto: dict = {}

    class AgenteFalso:
        def __init__(self, motor, modelo, **kw):
            visto.update(kw)

        def run(self, tarea, contexto):
            visto["tarea"] = tarea
            return SimpleNamespace(
                content="Encontré una inyección en api.py:12", tool_results=[], turns=1
            )

    from ai_architect.agente import orquestador

    monkeypatch.setattr(orquestador, "OrchestratorAgent", AgenteFalso)
    motor = SimpleNamespace(soporta_herramientas=lambda: True, modelo="x")

    r = herramientas.EspecialistaTool(str(tmp_path), motor).execute(
        nombre="security-reviewer", tarea="revisa la API"
    )

    assert r.success and "inyección" in r.content and "security-reviewer" in r.content
    assert (
        "security reviewer" in visto["system_prompt"]
        and visto["tarea"] == "revisa la API"
    )
    assert visto["interactive"] is False
    nombres = {h.spec.name for h in visto["tools"]}
    assert "file_read" in nombres and not nombres & {
        "file_write",
        "shell_exec",
        "git_commit",
        "ordenar",
    }


def test_especialista_desconocido(instalada, tmp_path: Path) -> None:
    r = herramientas.EspecialistaTool(str(tmp_path)).execute(
        nombre="cocinero", tarea="x"
    )

    assert not r.success and "No hay" in r.content


def test_las_herramientas_entran_en_la_caja_y_el_guion(
    instalada, tmp_path: Path
) -> None:
    from ai_architect.agente import caja
    from ai_architect.agente.guion import prompt_sistema

    nombres = set(caja.nombres(caja.herramientas_para(tmp_path)))
    assert {
        "buscar_habilidad",
        "usar_habilidad",
        "anexo_habilidad",
        "especialista",
    } <= nombres

    texto = prompt_sistema(tmp_path, "Efraín", False)
    assert "BIBLIOTECA" in texto and "2 habilidades" in texto


# --- por voz -----------------------------------------------------------------------------


def test_por_voz_busca_y_cuenta(instalada) -> None:
    salida = por_voz_.por_voz("¿Qué habilidades tienes para seguridad en Django?")
    assert salida is not None and "django-security" in salida["respuesta"]

    salida = por_voz_.por_voz("cuántas habilidades tienes")
    assert (
        "2 habilidades" in salida["respuesta"]
        and "2 especialistas" in salida["respuesta"]
    )

    assert por_voz_.por_voz("abre Word") is None


def test_por_voz_usa_una_habilidad_delegando_en_hacer(instalada) -> None:
    salida = por_voz_.por_voz(
        "usa la habilidad tdd-workflow y añade pruebas al módulo de voz"
    )

    assert "usar_habilidad" in salida["hacer"] and "tdd-workflow" in salida["hacer"]
    assert "módulo de voz" in salida["hacer"]
    assert "No tengo" in por_voz_.por_voz("usa la habilidad volar")["respuesta"]


def test_por_voz_delega_en_el_especialista(instalada) -> None:
    salida = por_voz_.por_voz("que el especialista de seguridad revise el proyecto")

    assert 'especialista(nombre="security-reviewer"' in salida["hacer"]
    assert "revise el proyecto" in salida["hacer"]

    salida = por_voz_.por_voz("dile al especialista python-reviewer que revise la voz")
    assert 'nombre="python-reviewer"' in salida["hacer"]


def test_por_voz_instala_y_no_repite(monkeypatch, fuente: Path) -> None:
    monkeypatch.setenv("ARCHITECT_BIBLIOTECA", str(fuente))

    assert "instalada" in por_voz_.por_voz("instala la biblioteca")["respuesta"]
    assert "Ya tengo" in por_voz_.por_voz("instala la biblioteca")["respuesta"]
    assert "actualizada" in por_voz_.por_voz("actualiza la biblioteca")["respuesta"]


def test_pide_ejecuta_lo_que_la_biblioteca_manda_a_hacer(
    instalada, tmp_path: Path, monkeypatch
) -> None:
    from ai_architect.commands import hacer, pide

    visto = {}

    def hacer_falso(project, frase, si=False, **kw):
        visto["frase"] = frase
        return {
            "success": True,
            "executed": False,
            "command": "hacer",
            "explanation": "Hecho.",
        }

    monkeypatch.setattr(hacer, "run", hacer_falso)
    monkeypatch.setattr(
        "ai_architect.commands.configurar.esta_configurado", lambda *a, **k: True
    )
    pide.conciso(False)

    salida = pide.run(
        str(tmp_path),
        "usa la habilidad tdd-workflow para el módulo de voz",
        engine=object(),
    )

    assert "usar_habilidad" in visto["frase"] and salida["explanation"].startswith(
        "Hecho"
    )
