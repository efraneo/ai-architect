"""La auditoría de seguridad: escáneres reales (doblados aquí), informe y las
órdenes que Architect orquesta después."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect import auditoria
from ai_architect.agents import ordenes


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "app" / "web.py").write_text(
        "import subprocess\n"
        "def correr(orden):\n"
        "    return subprocess.run(orden, shell=True)\n"
        "def cargar(datos):\n"
        "    import pickle\n"
        "    return pickle.loads(datos)\n"
        "password = 'secreta123'\n"
        "requests.get(url, verify=False)\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_web.py").write_text("eval('1')\n", encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def _sin_escaneres_externos(monkeypatch):
    monkeypatch.setattr(auditoria, "hay", lambda p: False)
    monkeypatch.setattr(auditoria, "modulo_disponible", lambda raiz, m: False)
    monkeypatch.setattr(auditoria, "correr_json", lambda orden, cwd, timeout=120: None)
    monkeypatch.setenv("ARCHITECT_SIN_INSTALAR", "1")


def test_los_patrones_peligrosos_se_ven_sin_modelo(repo: Path) -> None:
    hallazgos = auditoria.patrones_peligrosos(repo)

    que = {h["que"] for h in hallazgos}
    assert any("shell=True" in q for q in que)
    assert any("pickle" in q for q in que)
    assert any("TLS" in q for q in que)
    assert any("contraseña" in q for q in que)
    assert all(h["archivo"].startswith("app") for h in hallazgos)  # tests/ no cuenta
    assert hallazgos[0]["linea"] and hallazgos[0]["detalle"]


def test_escanear_junta_todo_y_guarda_el_informe(repo: Path) -> None:
    informe = auditoria.escanear(str(repo))

    assert informe["ok"] and informe["por_severidad"]["critica"] >= 1
    assert informe["hallazgos"][0]["severidad"] == "critica"
    assert set(informe["escaneres"]) == set(auditoria.ESCANERES)
    assert (
        Path(informe["archivo"]).is_file() and Path(informe["archivo"]).suffix == ".md"
    )
    assert auditoria.ultima() is not None and auditoria.ultima()["proyecto"] == str(
        repo.resolve()
    )
    palabras = auditoria.en_palabras(informe)
    assert "hallazgo" in palabras and "critica" in palabras


def test_un_escaner_roto_no_calla_a_los_demas(repo: Path, monkeypatch) -> None:
    def explota(raiz):
        raise RuntimeError("sin red")

    monkeypatch.setitem(auditoria.ESCANERES, "dependencias", explota)

    informe = auditoria.escanear(str(repo))

    assert str(informe["escaneres"]["dependencias"]).startswith("falló")
    assert informe["escaneres"]["patrones"] >= 3


def test_bandit_y_pip_audit_se_leen_si_estan(repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(auditoria, "modulo_disponible", lambda raiz, m: True)

    def json_falso(orden, cwd, timeout=120):
        if "bandit" in orden:
            return {
                "results": [
                    {
                        "issue_severity": "HIGH",
                        "test_id": "B602",
                        "issue_text": "shell=True",
                        "filename": "app/web.py",
                        "line_number": 3,
                        "code": "...",
                    }
                ]
            }
        if "pip_audit" in orden:
            return {
                "dependencies": [
                    {
                        "name": "requests",
                        "version": "2.0",
                        "vulns": [
                            {
                                "id": "PYSEC-1",
                                "fix_versions": ["2.32.0"],
                                "description": "x",
                            }
                        ],
                    }
                ]
            }
        return None

    monkeypatch.setattr(auditoria, "correr_json", json_falso)

    b = auditoria.bandit(repo)
    assert b and b[0]["severidad"] == "alta" and "B602" in b[0]["que"]

    p = auditoria.pip_audit(repo)
    assert p and "PYSEC-1" in p[0]["que"] and "2.32.0" in p[0]["detalle"]


def test_sin_bandit_no_se_instala_en_las_pruebas(repo: Path) -> None:
    assert auditoria.bandit(repo) == []
    assert auditoria.pip_audit(repo) == []
    assert auditoria.npm_audit(repo) == []
    assert auditoria.agentshield(repo) == []


def test_npm_audit_y_agentshield(repo: Path, monkeypatch) -> None:
    (repo / "package.json").write_text("{}", encoding="utf-8")
    (repo / ".claude").mkdir()
    monkeypatch.setattr(auditoria, "hay", lambda p: True)

    def json_falso(orden, cwd, timeout=120):
        if orden[0] == "npm":
            return {
                "vulnerabilities": {
                    "lodash": {
                        "severity": "high",
                        "range": "<4.17",
                        "via": [{"title": "Prototype pollution"}],
                    }
                }
            }
        if "ecc-agentshield" in orden:
            return {
                "findings": [
                    {
                        "severity": "critical",
                        "title": "Bash(*) permitido",
                        "file": "settings.json",
                    }
                ]
            }
        return None

    monkeypatch.setattr(auditoria, "correr_json", json_falso)

    n = auditoria.npm_audit(repo)
    assert n and n[0]["severidad"] == "alta" and "lodash" in n[0]["que"]

    a = auditoria.agentshield(repo)
    assert a and a[0]["severidad"] == "critica" and "Bash" in a[0]["que"]


def test_por_voz_manda_a_atacar_y_a_corregir(repo: Path) -> None:
    salida = auditoria.por_voz("Hackea el proyecto")
    assert (
        salida is not None
        and "consultar" in salida["hacer"]
        and "security-reviewer" in salida["hacer"]
    )
    assert "No cambies nada" in salida["hacer"]

    salida = auditoria.por_voz("corrige los agujeros")
    assert "prueba que falle" in salida["hacer"] and "permiso" in salida["hacer"]

    assert auditoria.por_voz("abre Word") is None
    assert "Todavía no" in auditoria.por_voz("última auditoría")["respuesta"]

    auditoria.escanear(str(repo))
    assert "hallazgo" in auditoria.por_voz("qué encontró la auditoría")["respuesta"]
    assert (
        auditoria.ultima()["archivo"]
        in auditoria.por_voz("corrige los agujeros")["hacer"]
    )


def test_la_orden_seguridad_auditar_corre_los_escaneres(repo: Path) -> None:
    salida = ordenes.ejecutar("seguridad", "auditar", str(repo))

    assert (
        salida["ok"]
        and "hallazgo" in salida["hecho"]
        and salida["por_severidad"]["critica"] >= 1
    )
    assert ordenes.tareas_de("seguridad")["auditar"].cambia is False

    ultima = ordenes.ejecutar("seguridad", "ultima_auditoria", str(repo))
    assert ultima["ok"] and ultima["archivo"]


def test_el_informe_en_markdown_lista_por_severidad(repo: Path) -> None:
    informe = auditoria.escanear(str(repo))
    texto = auditoria.en_markdown(informe)

    assert texto.startswith("# Auditoría de seguridad") and "| critica |" in texto
    assert "**critica**" in texto and "app" in texto


def test_respuestas_atiende_la_auditoria() -> None:
    from ai_architect.commands import respuestas

    salida = respuestas.responder("audita la seguridad")

    assert salida is not None and salida.get("hacer")
