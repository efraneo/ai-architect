"""La auditoría de seguridad: Architect ataca su propio proyecto antes que otro.

«Hackea el proyecto», «busca agujeros», «audita la seguridad». Dos mitades:

1. **Escáneres reales**, sin modelo: secretos en el código y en git, paquetes
   con vulnerabilidades conocidas (osv.dev, pip-audit, npm audit), errores
   latentes (ruff), patrones peligrosos (eval, pickle, shell=True, verify=False,
   claves débiles, DEBUG en producción…), bandit para Python y AgentShield para
   la configuración de agentes (`.claude/`). Lo que falte y se pueda instalar,
   Architect lo instala (pip-audit, bandit) si se le permite.
2. **Los especialistas** de la biblioteca (security-reviewer, y la habilidad
   security-bounty-hunter) para lo que un escáner no ve: inyección, SSRF,
   auth rota, deserialización, rutas alcanzables desde fuera. Eso lo orquesta
   Architect con `especialista` y `usar_habilidad` a partir de estos hallazgos.

El informe se guarda en ``~/.ai_architect/auditorias/`` y se corrige con
«corrige los agujeros»: cada hallazgo se reproduce con una prueba, se parchea
con permiso y se corren las pruebas.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_architect.agents.herramientas_externas import (
    correr,
    correr_json,
    hay,
    modulo_disponible,
    python_de,
)
from ai_architect.core.texto import contiene, sin_adornos

SEVERIDADES = ("critica", "alta", "media", "baja")

PIDE = (
    "audita la seguridad",
    "auditoria de seguridad",
    "hackea el proyecto",
    "hackea este proyecto",
    "hackeate",
    # Como lo transcribe el oído cuando lo oye mal:
    "haquea el proyecto",
    "jaquea el proyecto",
    "hakea el proyecto",
    "jakea el proyecto",
    "hackea el codigo",
    "haquea el codigo",
    "jaquea el codigo",
    "hackealo",
    "haquealo",
    "jaquealo",
    "ataca el proyecto",
    "busca agujeros",
    "busca vulnerabilidades",
    "busca fallos de seguridad",
    "revisa la seguridad a fondo",
    "pon a prueba la seguridad",
    "prueba de penetracion",
    "pentest",
    "que tan seguro es el proyecto",
    "es seguro el proyecto",
)

# «Hackea», «haquea», «jaquea», «hakéalo»: como lo oiga, es lo mismo.
HACKEA = re.compile(r"^(?:h|j)a[ckq]{1,3}e+a(?:lo|me|te)?(?:\s|$)")

CORRIGE = (
    "corrige los agujeros",
    "corrige los errores de seguridad",
    "corrige los errores encontrados",
    "corrige los errores",
    "arregla los errores",
    "parcha los agujeros",
    "parchea los agujeros",
    "corrige las vulnerabilidades",
    "parcha las vulnerabilidades",
    "arregla la seguridad",
    "corrige la seguridad",
    "parcha la seguridad",
    "arregla lo que encontraste",
    "corrige lo que encontraste",
    "cierra los agujeros",
)

# Patrones que un atacante busca primero. (regex, severidad, qué es)
PATRONES: tuple[tuple[str, str, str], ...] = (
    (r"\beval\(", "alta", "eval() ejecuta lo que le llegue"),
    (r"\bexec\(", "alta", "exec() ejecuta lo que le llegue"),
    (r"pickle\.loads?\(", "alta", "pickle deserializa código: nunca con datos ajenos"),
    (r"yaml\.load\((?![^)]*Loader)", "alta", "yaml.load sin Loader seguro"),
    (r"shell\s*=\s*True", "media", "subprocess con shell=True: inyección de comandos"),
    (r"os\.system\(", "media", "os.system: inyección de comandos"),
    (r"verify\s*=\s*False", "media", "TLS sin verificar el certificado"),
    (r"\bmd5\(|\bsha1\(", "baja", "md5/sha1 no sirven para contraseñas ni firmas"),
    (r"DEBUG\s*=\s*True", "media", "DEBUG=True enseña trazas y secretos"),
    (r"0\.0\.0\.0", "baja", "escucha en todas las interfaces"),
    (r"chmod\s+777|0o777", "media", "permisos abiertos a todos"),
    (r"innerHTML\s*=", "media", "innerHTML con datos: XSS"),
    (r"dangerouslySetInnerHTML", "media", "HTML sin escapar en React: XSS"),
    (
        r"\bexecute\((?:f\"|f'|\"[^\"]*\"\s*%|'[^']*'\s*%|[^)]*\+)",
        "alta",
        "SQL armado con concatenación: inyección",
    ),
    (
        r"password\s*=\s*['\"][^'\"]{4,}['\"]",
        "critica",
        "contraseña escrita en el código",
    ),
    (
        r"(?:api[_-]?key|secret|token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
        "critica",
        "clave escrita en el código",
    ),
    (r"\bcurl\b[^\n|]*\|\s*(?:ba)?sh\b", "alta", "curl | sh: ejecuta lo que baje"),
    (
        r"npx\s+-y\s+(?!ecc-agentshield)[\w@/.-]+(?![\w@/.-]*@\d)",
        "baja",
        "npx -y sin versión fija: cadena de suministro",
    ),
    (
        r"allow_origins\s*=\s*\[\s*['\"]\*['\"]",
        "media",
        "CORS abierto a cualquier origen",
    ),
    (r"algorithms?\s*=\s*\[?\s*['\"]none['\"]", "critica", "JWT con algoritmo none"),
)

EXTENSIONES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".sh",
    ".ps1",
    ".cmd",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".env",
    ".html",
}

CARPETAS_AJENAS = {
    ".venv",
    "venv",
    "node_modules",
    ".git",
    "dist",
    "build",
    "salida",
    "dist_tmp",
    "build_tmp",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    "biblioteca",
}


def ruta_informes() -> Path:
    from ai_architect.agente.rutas_agente import get_config_dir

    return Path(get_config_dir()) / "auditorias"


# --- escáneres --------------------------------------------------------------------------


def _hallazgo(
    fuente: str,
    severidad: str,
    que: str,
    archivo: str = "",
    linea: int | None = None,
    detalle: str = "",
) -> dict[str, Any]:
    return {
        "fuente": fuente,
        "severidad": severidad if severidad in SEVERIDADES else "media",
        "que": que[:200],
        "archivo": archivo,
        "linea": linea,
        "detalle": detalle[:300],
    }


def _archivos(raiz: Path) -> list[Path]:
    salida = []

    for archivo in raiz.rglob("*"):
        if not archivo.is_file() or archivo.suffix.lower() not in EXTENSIONES:
            continue

        if any(parte in CARPETAS_AJENAS for parte in archivo.relative_to(raiz).parts):
            continue

        if (
            archivo.name.startswith("test_")
            or "/tests/" in archivo.as_posix()
            or "\\tests\\" in str(archivo)
        ):
            continue

        salida.append(archivo)

    return salida[:4000]


def patrones_peligrosos(raiz: Path) -> list[dict[str, Any]]:
    """Lo que un atacante busca con grep: en segundos, sin modelo."""
    compilados = [(re.compile(p), s, q) for p, s, q in PATRONES]
    hallazgos = []
    propio = Path(__file__).resolve()

    for archivo in _archivos(raiz):
        if archivo.resolve() == propio:
            continue

        try:
            lineas = archivo.read_text(encoding="utf-8", errors="ignore").splitlines()

        except OSError:
            continue

        for numero, texto in enumerate(lineas, 1):
            recortado = texto.lstrip()

            # Un comentario que describe el peligro no es el peligro.
            if (
                "noqa: S" in texto
                or "# seguro" in texto
                or recortado.startswith(("#", "//", "*", "<!--", "rem ", "REM "))
            ):
                continue

            for patron, severidad, que in compilados:
                if patron.search(texto):
                    hallazgos.append(
                        _hallazgo(
                            "patrones",
                            severidad,
                            que,
                            str(archivo.relative_to(raiz)),
                            numero,
                            texto.strip()[:160],
                        )
                    )

                    break

    return hallazgos[:200]


def secretos(raiz: Path) -> list[dict[str, Any]]:
    from ai_architect.agents.security_agent import SecurityAgent

    informe = SecurityAgent().review(str(raiz))
    salida = []

    for h in informe.get("findings") or []:
        if isinstance(h, dict):
            salida.append(
                _hallazgo(
                    "secretos",
                    "critica",
                    str(h.get("type") or h.get("issue", "secreto")),
                    str(h.get("file", "")),
                    h.get("line"),
                    str(h.get("issue", "")),
                )
            )

    return salida


def dependencias(raiz: Path) -> list[dict[str, Any]]:
    from ai_architect.agents.dependency_agent import DependencyAgent

    informe = DependencyAgent().review(str(raiz))
    salida = []

    for h in informe.get("findings") or []:
        if not isinstance(h, dict):
            continue

        tipo = str(h.get("type", ""))
        vulnerable = "vuln" in tipo or "osv" in tipo or "CVE" in str(h.get("issue", ""))
        salida.append(
            _hallazgo(
                "dependencias",
                "alta" if vulnerable else "baja",
                tipo or "dependencia",
                str(h.get("file", "")),
                None,
                str(h.get("issue", "")),
            )
        )

    return salida


def errores_latentes(raiz: Path) -> list[dict[str, Any]]:
    from ai_architect.agents.bug_hunter_agent import BugHunterAgent

    informe = BugHunterAgent().review(str(raiz))

    return [
        _hallazgo(
            "errores",
            "media",
            str(h.get("type", "error")),
            str(h.get("file", "")),
            h.get("line"),
            str(h.get("issue", "")),
        )
        for h in (informe.get("findings") or [])
        if isinstance(h, dict)
    ][:60]


def _asegurar(raiz: Path, modulo: str, paquete: str) -> bool:
    """Instala un escáner de Python si falta y se permite (Architect se procura lo suyo)."""
    if modulo_disponible(raiz, modulo):
        return True

    if os.getenv("ARCHITECT_SIN_INSTALAR", "").strip() == "1":
        return False

    try:
        from ai_architect import instalar

        return bool(
            instalar.paquete(paquete, raiz / "requirements.txt").get("ok")
        ) and modulo_disponible(raiz, modulo)

    except Exception:  # noqa: BLE001 - sin instalar, sin escáner
        return False


def bandit(raiz: Path) -> list[dict[str, Any]]:
    """bandit sobre el paquete principal: lo que ruff no mira (inyección, cripto, tmp)."""
    if not list(raiz.glob("*.py")) and not any(raiz.glob("*/__init__.py")):
        return []

    if not _asegurar(raiz, "bandit", "bandit"):
        return []

    from ai_architect.agents.calidad_agent import _paquete_principal

    objetivo = _paquete_principal(raiz) or "."
    datos = correr_json(
        [
            python_de(raiz),
            "-m",
            "bandit",
            "-q",
            "-r",
            objetivo,
            "-f",
            "json",
            "-x",
            ".venv,tests,node_modules",
        ],
        raiz,
        300,
    )
    niveles = {"HIGH": "alta", "MEDIUM": "media", "LOW": "baja"}
    salida = []

    for r in (datos or {}).get("results", []) if isinstance(datos, dict) else []:
        if not isinstance(r, dict):
            continue

        salida.append(
            _hallazgo(
                "bandit",
                niveles.get(str(r.get("issue_severity")), "media"),
                f"{r.get('test_id', '')} {r.get('issue_text', '')}",
                str(r.get("filename", "")),
                r.get("line_number"),
                str(r.get("code", ""))[:160],
            )
        )

    return salida[:80]


def pip_audit(raiz: Path) -> list[dict[str, Any]]:
    if (
        not (raiz / "requirements.txt").is_file()
        and not (raiz / "pyproject.toml").is_file()
    ):
        return []

    if not _asegurar(raiz, "pip_audit", "pip-audit"):
        return []

    datos = correr_json(
        [python_de(raiz), "-m", "pip_audit", "-f", "json", "--progress-spinner", "off"],
        raiz,
        300,
    )
    salida = []
    lista = (
        datos.get("dependencies", [])
        if isinstance(datos, dict)
        else datos if isinstance(datos, list) else []
    )

    for d in lista:
        if not isinstance(d, dict):
            continue

        for v in d.get("vulns", []) or []:
            salida.append(
                _hallazgo(
                    "pip-audit",
                    "alta",
                    f"{d.get('name')} {d.get('version')}: {v.get('id', '')}",
                    "requirements.txt",
                    None,
                    f"arregla en {', '.join(v.get('fix_versions') or []) or '?'}: {str(v.get('description', ''))[:120]}",
                )
            )

    return salida[:80]


def npm_audit(raiz: Path) -> list[dict[str, Any]]:
    if not (raiz / "package.json").is_file() or not hay("npm"):
        return []

    datos = correr_json(["npm", "audit", "--json"], raiz, 180)

    if not isinstance(datos, dict):
        return []

    niveles = {
        "critical": "critica",
        "high": "alta",
        "moderate": "media",
        "low": "baja",
    }
    salida = []

    for nombre, v in (datos.get("vulnerabilities") or {}).items():
        if isinstance(v, dict):
            salida.append(
                _hallazgo(
                    "npm-audit",
                    niveles.get(str(v.get("severity")), "media"),
                    f"{nombre} {v.get('range', '')}",
                    "package.json",
                    None,
                    "; ".join(
                        str(x.get("title", x)) if isinstance(x, dict) else str(x)
                        for x in (v.get("via") or [])[:2]
                    ),
                )
            )

    return salida[:80]


def agentshield(raiz: Path) -> list[dict[str, Any]]:
    """La configuración de agentes (.claude) también es superficie de ataque."""
    objetivos = [p for p in (raiz / ".claude", Path.home() / ".claude") if p.is_dir()]

    if not objetivos or not hay("npx"):
        return []

    salida = []

    for objetivo in objetivos[:2]:
        datos = correr_json(
            [
                "npx",
                "-y",
                "ecc-agentshield",
                "scan",
                "--path",
                str(objetivo),
                "--format",
                "json",
            ],
            raiz,
            240,
        )

        if not isinstance(datos, dict):
            continue

        for f in datos.get("findings") or datos.get("issues") or []:
            if not isinstance(f, dict):
                continue

            niveles = {
                "critical": "critica",
                "high": "alta",
                "medium": "media",
                "low": "baja",
            }
            salida.append(
                _hallazgo(
                    "agentshield",
                    niveles.get(str(f.get("severity", "")).lower(), "media"),
                    str(f.get("title") or f.get("rule") or f.get("message", "")),
                    str(f.get("file") or objetivo),
                    f.get("line"),
                    str(f.get("description") or f.get("fix") or "")[:200],
                )
            )

    return salida[:60]


ESCANERES = {
    "secretos": secretos,
    "patrones": patrones_peligrosos,
    "dependencias": dependencias,
    "errores": errores_latentes,
    "bandit": bandit,
    "pip-audit": pip_audit,
    "npm-audit": npm_audit,
    "agentshield": agentshield,
}


# --- la auditoría --------------------------------------------------------------------------


def escanear(project: str, solo: tuple[str, ...] = ()) -> dict[str, Any]:
    """Todos los escáneres reales. Uno roto no calla a los demás."""
    raiz = Path(project).resolve()
    hallazgos: list[dict[str, Any]] = []
    corridos: dict[str, int | str] = {}

    for nombre, escaner in ESCANERES.items():
        if solo and nombre not in solo:
            continue

        try:
            encontrados = escaner(raiz)
            hallazgos.extend(encontrados)
            corridos[nombre] = len(encontrados)

        except Exception as e:  # noqa: BLE001 - se cuenta y se sigue
            corridos[nombre] = f"falló: {e}"

    hallazgos.sort(key=lambda h: SEVERIDADES.index(h["severidad"]))
    informe = {
        "ok": True,
        "proyecto": str(raiz),
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "escaneres": corridos,
        "por_severidad": {
            s: sum(1 for h in hallazgos if h["severidad"] == s) for s in SEVERIDADES
        },
        "hallazgos": hallazgos,
    }
    informe["archivo"] = guardar(informe)

    return informe


def guardar(informe: dict[str, Any]) -> str:
    carpeta = ruta_informes()

    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        nombre = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        archivo = carpeta / f"{nombre}.md"
        informe["archivo"] = str(archivo)
        (carpeta / f"{nombre}.json").write_text(
            json.dumps(informe, ensure_ascii=False, indent=1, default=str),
            encoding="utf-8",
        )
        archivo.write_text(en_markdown(informe), encoding="utf-8")

        return str(archivo)

    except OSError:
        return ""


def ultima() -> dict[str, Any] | None:
    carpeta = ruta_informes()

    try:
        archivos = sorted(carpeta.glob("*.json"))

    except OSError:
        return None

    if not archivos:
        return None

    try:
        datos = json.loads(archivos[-1].read_text(encoding="utf-8"))

        return datos if isinstance(datos, dict) else None

    except (OSError, ValueError):
        return None


def en_markdown(informe: dict[str, Any]) -> str:
    lineas = [
        f"# Auditoría de seguridad · {informe.get('fecha', '')}",
        "",
        f"Proyecto: `{informe.get('proyecto', '')}`",
        "",
        "Escáneres: "
        + ", ".join(f"{k} ({v})" for k, v in (informe.get("escaneres") or {}).items()),
        "",
        "| Severidad | Cuántos |",
        "|---|---|",
    ]

    for s in SEVERIDADES:
        lineas.append(f"| {s} | {informe.get('por_severidad', {}).get(s, 0)} |")

    lineas += ["", "## Hallazgos", ""]

    for h in informe.get("hallazgos") or []:
        sitio = h.get("archivo", "")

        if sitio and h.get("linea"):
            sitio = f"{sitio}:{h['linea']}"

        lineas.append(
            f"- **{h['severidad']}** [{h['fuente']}] {h['que']}"
            + (f" — `{sitio}`" if sitio else "")
            + (f"\n  {h['detalle']}" if h.get("detalle") else "")
        )

    return "\n".join(lineas) + "\n"


def en_palabras(informe: dict[str, Any]) -> str:
    por = informe.get("por_severidad") or {}
    total = sum(por.values())

    if not total:
        return "Los escáneres no encontraron nada: ni secretos, ni paquetes vulnerables, ni patrones peligrosos."

    partes = [f"{n} {s}" for s in SEVERIDADES if (n := por.get(s, 0))]
    primeros = "; ".join(
        f"{h['que']}" + (f" en {h['archivo']}" if h.get("archivo") else "")
        for h in (informe.get("hallazgos") or [])[:3]
    )

    return f"Encontré {total} hallazgo(s): {', '.join(partes)}. Lo primero: {primeros}."


# --- lo que Architect orquesta después -----------------------------------------------------


def orden_de_auditoria(project: str) -> str:
    return (
        "Haz una auditoría de seguridad completa del repositorio, como un atacante que quiere entrar. "
        '1) Usa consultar(agente="seguridad", tarea="auditar") para correr los escáneres reales '
        "(secretos, patrones peligrosos, dependencias vulnerables, bandit, pip-audit, npm audit, configuración de agentes). "
        '2) Con esos hallazgos, delega en especialista(nombre="security-reviewer", tarea=...) y sigue la habilidad '
        "security-bounty-hunter (usar_habilidad) para lo que un escáner no ve: inyección, SSRF, autenticación rota, "
        "deserialización, rutas alcanzables desde fuera; lee el código de verdad, no supongas. "
        "3) Entrega un informe priorizado por severidad, con archivo y línea, cómo se explotaría y cómo se corrige. "
        "No cambies nada en este paso."
    )


def orden_de_correccion(project: str) -> str:
    informe = ultima()
    referencia = (
        f" El último informe está en {informe.get('archivo')}."
        if informe and informe.get("archivo")
        else ""
    )

    return (
        "Corrige los hallazgos de seguridad de la última auditoría, de mayor a menor severidad."
        + referencia
        + " Para cada uno: reproduce el problema con una prueba que falle, aplica el parche mínimo, "
        "vuelve a correr esa prueba y luego toda la batería (consultar pruebas correr). "
        "Si un arreglo exige una decisión de diseño, propónla y sigue con el siguiente. "
        "Cada cambio pasa por permiso: no te lo saltes."
    )


def por_voz(frase: str) -> dict[str, Any] | None:
    limpia = sin_adornos(frase)

    if not limpia:
        return None

    if contiene(limpia, *CORRIGE):
        return {
            "respuesta": "Voy a corregir lo que encontró la auditoría, con tu permiso en cada cambio.",
            "hacer": orden_de_correccion("."),
        }

    if contiene(limpia, *PIDE) or HACKEA.match(limpia):
        return {
            "respuesta": "Voy a atacar el proyecto: escáneres reales y luego los especialistas.",
            "hacer": orden_de_auditoria("."),
        }

    if limpia in (
        "ultima auditoria",
        "que encontro la auditoria",
        "resultado de la auditoria",
        "informe de seguridad",
    ):
        informe = ultima()

        if informe is None:
            return {
                "respuesta": "Todavía no he hecho ninguna auditoría. Di «audita la seguridad»."
            }

        return {
            "respuesta": en_palabras(informe),
            "panel": {
                "tipo": "texto",
                "titulo": "Última auditoría",
                "cuerpo": en_markdown(informe)[:4000],
            },
        }

    return None


def herramientas_disponibles(raiz: Path) -> dict[str, bool]:
    return {
        "bandit": modulo_disponible(raiz, "bandit"),
        "pip-audit": modulo_disponible(raiz, "pip_audit"),
        "npm": hay("npm"),
        "agentshield (npx)": hay("npx"),
        "git": bool(shutil.which("git")),
    }


__all__ = [
    "escanear",
    "ultima",
    "en_palabras",
    "en_markdown",
    "por_voz",
    "orden_de_auditoria",
    "orden_de_correccion",
    "herramientas_disponibles",
    "correr",
]
