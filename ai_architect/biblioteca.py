"""La biblioteca: especialistas, habilidades y reglas que Architect tiene a mano.

Cientos de habilidades (SKILL.md), decenas de especialistas (personas en
markdown con nombre, descripción y herramientas) y reglas por lenguaje viven
en ``~/.ai_architect/biblioteca``. No entran todas en la caja del agente
(serían cientos de herramientas para el modelo): se buscan por tema y se
cargan cuando hacen falta.

    tú   ¿Qué habilidades tienes para seguridad en Django?
    él   Tengo 4: django-security, security-review, …
    tú   Usa la habilidad django-security y revisa el proyecto.

Se instala o actualiza desde un repositorio de GitHub (por defecto el que
está en ``ARCHITECT_BIBLIOTECA``) o desde una carpeta local. La atribución
de lo que venga de terceros va en ``docs/LICENCIAS-TERCEROS.md``.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_architect.core.texto import sin_adornos

ORIGEN_POR_DEFECTO = "https://github.com/affaan-m/ECC"

CARPETAS = ("agents", "skills", "rules", "commands")
NOMBRES = {
    "agents": "especialistas",
    "skills": "habilidades",
    "rules": "reglas",
    "commands": "recetas",
}

PALABRAS_VACIAS = {
    "de",
    "la",
    "el",
    "los",
    "las",
    "para",
    "con",
    "que",
    "and",
    "the",
    "for",
    "with",
    "use",
    "when",
    "this",
    "your",
    "you",
    "a",
    "an",
    "of",
    "to",
    "in",
    "on",
    "or",
    "en",
    "un",
    "una",
    "del",
    "al",
    "y",
    "o",
}

SINONIMOS = {
    "seguridad": ("security", "secure", "vulnerab", "owasp", "auth", "secret"),
    "pruebas": ("test", "tdd", "e2e", "coverage"),
    "rendimiento": ("performance", "perf", "latency", "cache", "optimi"),
    "base de datos": ("database", "sql", "postgres", "prisma", "migration"),
    "despliegue": ("deploy", "docker", "kubernetes", "ci", "cd"),
    "documentacion": ("doc", "readme", "adr"),
    "diseno": ("design", "ui", "ux", "frontend", "motion", "a11y"),
    "api": ("api", "rest", "endpoint", "fastapi", "nestjs"),
    "planificacion": ("plan", "prd", "spec", "architecture"),
    "revision": ("review", "reviewer", "quality", "lint"),
    "python": ("python", "django", "fastapi", "pytest"),
    "javascript": ("typescript", "javascript", "react", "vue", "nextjs", "node"),
    "movil": ("android", "kotlin", "swift", "ios", "flutter", "react-native"),
    "investigacion": ("research", "search", "scholar", "market"),
    "marketing": ("marketing", "seo", "content", "brand", "social"),
    "redes": ("network", "bgp", "vlan", "wireguard", "cisco"),
}

_indice: dict[str, Any] | None = None
_indice_de: str = ""


def _clave(nombre: str) -> str:
    """«django security», «django-security» y «Django_Security» son la misma."""
    return re.sub(r"[\s_-]+", "", sin_adornos(nombre))


def ruta() -> Path:
    from ai_architect.agente.rutas_agente import get_config_dir

    return Path(get_config_dir()) / "biblioteca"


def instalada() -> bool:
    return (ruta() / "skills").is_dir() or (ruta() / "agents").is_dir()


# --- instalar ---------------------------------------------------------------------


def _origen() -> str:
    return os.getenv("ARCHITECT_BIBLIOTECA", "").strip() or ORIGEN_POR_DEFECTO


def instalar(origen: str = "", destino: Path | None = None) -> dict[str, Any]:
    """Trae especialistas, habilidades, reglas y recetas desde GitHub o una carpeta.

    Solo se copian las cuatro carpetas de contenido (markdown y sus anexos):
    ni scripts, ni ganchos, ni configuración de otros programas.
    """
    global _indice

    origen = (origen or _origen()).strip()
    base = destino or ruta()

    try:
        if origen.startswith(("http://", "https://")):
            cuenta = _desde_github(origen, base)

        else:
            cuenta = _desde_carpeta(Path(origen), base)

    except Exception as e:  # noqa: BLE001 - sin red o sin carpeta se dice
        return {"ok": False, "error": f"no pude instalar la biblioteca: {e}"}

    if not any(cuenta.values()):
        return {"ok": False, "error": "ahí no hay especialistas ni habilidades"}

    (base / "origen.json").write_text(
        json.dumps(
            {
                "origen": origen,
                "fecha": datetime.now().isoformat(timespec="seconds"),
                "cuenta": cuenta,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _indice = None

    try:
        from ai_architect import instalar as instalar_

        instalar_._apuntar("biblioteca", origen, json.dumps(cuenta))

    except Exception:  # noqa: BLE001 - el registro es un extra
        pass

    return {"ok": True, "origen": origen, "carpeta": str(base), **cuenta}


GITHUB = re.compile(
    r"^https?://github\.com/(?P<usuario>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?(?:/tree/(?P<rama>[\w.-]+))?/?$"
)


def _desde_github(url: str, base: Path) -> dict[str, int]:
    import requests

    m = GITHUB.match(url)

    if not m:
        raise ValueError("dame la URL del repositorio de GitHub")

    usuario, repo = m["usuario"], m["repo"]
    ramas = [m["rama"]] if m["rama"] else ["main", "master"]
    respuesta = None

    for rama in ramas:
        respuesta = requests.get(
            f"https://codeload.github.com/{usuario}/{repo}/zip/refs/heads/{rama}",
            timeout=180,
        )

        if respuesta.status_code == 200:
            break

    if respuesta is None or respuesta.status_code != 200:
        raise ValueError(f"no pude bajar {usuario}/{repo}")

    paquete = zipfile.ZipFile(io.BytesIO(respuesta.content))
    raiz = paquete.namelist()[0].split("/")[0]
    cuenta = dict.fromkeys(CARPETAS, 0)

    for carpeta in CARPETAS:
        prefijo = f"{raiz}/{carpeta}/"
        destino = base / carpeta

        if destino.exists():
            shutil.rmtree(destino)

        for miembro in paquete.namelist():
            if not miembro.startswith(prefijo) or miembro.endswith("/"):
                continue

            relativo = Path(miembro[len(prefijo) :])

            if ".." in relativo.parts or not _vale(relativo):
                continue

            salida = destino / relativo
            salida.parent.mkdir(parents=True, exist_ok=True)
            salida.write_bytes(paquete.read(miembro))
            cuenta[carpeta] += 1

    return cuenta


def _desde_carpeta(origen: Path, base: Path) -> dict[str, int]:
    if not origen.is_dir():
        raise ValueError(f"no existe la carpeta {origen}")

    cuenta = dict.fromkeys(CARPETAS, 0)

    for carpeta in CARPETAS:
        fuente = origen / carpeta

        if not fuente.is_dir():
            continue

        destino = base / carpeta

        if destino.exists():
            shutil.rmtree(destino)

        for archivo in fuente.rglob("*"):
            if not archivo.is_file():
                continue

            relativo = archivo.relative_to(fuente)

            if not _vale(relativo):
                continue

            salida = destino / relativo
            salida.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archivo, salida)
            cuenta[carpeta] += 1

    return cuenta


def _vale(relativo: Path) -> bool:
    """Solo contenido: markdown, texto, json/yaml/toml de datos. Nada ejecutable."""
    return relativo.suffix.lower() in (
        ".md",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".csv",
    )


# --- leer ----------------------------------------------------------------------------


def _frontmatter(texto: str) -> tuple[dict[str, str], str]:
    if not texto.startswith("---"):
        return {}, texto

    partes = texto.split("---", 2)

    if len(partes) < 3:
        return {}, texto

    datos: dict[str, str] = {}

    for linea in partes[1].splitlines():
        if ":" in linea and not linea.startswith((" ", "\t")):
            clave, _, valor = linea.partition(":")
            datos[clave.strip()] = valor.strip().strip("\"'")

    return datos, partes[2].strip()


def _leer(archivo: Path) -> str:
    try:
        return archivo.read_text(encoding="utf-8", errors="replace")

    except OSError:
        return ""


def indice() -> dict[str, list[dict[str, Any]]]:
    """Todo lo que hay, con nombre y descripción: especialistas, habilidades, reglas, recetas."""
    global _indice, _indice_de

    base = ruta()

    if _indice is not None and _indice_de == str(base):
        return _indice

    salida: dict[str, list[dict[str, Any]]] = {n: [] for n in NOMBRES.values()}

    for archivo in (
        sorted((base / "agents").glob("*.md")) if (base / "agents").is_dir() else []
    ):
        datos, _ = _frontmatter(_leer(archivo))
        salida["especialistas"].append(
            {
                "nombre": datos.get("name") or archivo.stem,
                "descripcion": datos.get("description", "")[:300],
                "herramientas": datos.get("tools", ""),
                "modelo": datos.get("model", ""),
                "archivo": str(archivo),
            }
        )

    for carpeta in (
        sorted(p for p in (base / "skills").glob("*") if p.is_dir())
        if (base / "skills").is_dir()
        else []
    ):
        manifiesto = carpeta / "SKILL.md"

        if not manifiesto.is_file():
            continue

        datos, _ = _frontmatter(_leer(manifiesto))
        salida["habilidades"].append(
            {
                "nombre": datos.get("name") or carpeta.name,
                "descripcion": datos.get("description", "")[:300],
                "archivo": str(manifiesto),
                "anexos": sum(1 for _ in carpeta.rglob("*") if _.is_file()) - 1,
            }
        )

    for archivo in (
        sorted((base / "rules").rglob("*.md")) if (base / "rules").is_dir() else []
    ):
        if archivo.name.lower() == "readme.md":
            continue

        salida["reglas"].append(
            {
                "nombre": f"{archivo.parent.name}/{archivo.stem}",
                "descripcion": _primera_linea(_leer(archivo)),
                "archivo": str(archivo),
            }
        )

    for archivo in (
        sorted((base / "commands").glob("*.md")) if (base / "commands").is_dir() else []
    ):
        datos, cuerpo = _frontmatter(_leer(archivo))
        salida["recetas"].append(
            {
                "nombre": datos.get("name") or archivo.stem,
                "descripcion": (datos.get("description") or _primera_linea(cuerpo))[
                    :300
                ],
                "archivo": str(archivo),
            }
        )

    _indice = salida
    _indice_de = str(base)

    return salida


def _primera_linea(texto: str) -> str:
    for linea in texto.splitlines():
        limpia = linea.strip("# ").strip()

        if limpia and not limpia.startswith(("---", "<", "|")):
            return limpia[:200]

    return ""


def cuenta() -> dict[str, int]:
    return {tipo: len(lista) for tipo, lista in indice().items()}


# --- buscar y traer -------------------------------------------------------------------


def _claves(tema: str) -> list[str]:
    limpio = sin_adornos(tema)
    palabras = [
        p
        for p in re.findall(r"[a-z0-9]+", limpio)
        if p not in PALABRAS_VACIAS and len(p) > 2
    ]
    extra: list[str] = []

    for palabra in list(palabras) + [limpio]:
        if not palabra:
            continue

        for clave, sinonimos in SINONIMOS.items():
            if palabra == clave or palabra in clave or clave in limpio:
                extra.extend(sinonimos)

    return list(dict.fromkeys(palabras + extra))


def buscar(tema: str, tipo: str = "", maximo: int = 8) -> list[dict[str, Any]]:
    """Lo que más pega con el tema, por nombre y descripción."""
    claves = _claves(tema)

    if not claves:
        return []

    candidatos: list[tuple[int, dict[str, Any]]] = []

    for nombre_tipo, lista in indice().items():
        if tipo and nombre_tipo != tipo:
            continue

        for entrada in lista:
            nombre = sin_adornos(entrada["nombre"])
            descripcion = sin_adornos(entrada.get("descripcion", ""))
            puntos = 0

            for clave in claves:
                if clave in nombre:
                    puntos += 5

                if clave in descripcion:
                    puntos += 2

            if puntos:
                candidatos.append((puntos, {**entrada, "tipo": nombre_tipo}))

    candidatos.sort(key=lambda par: (-par[0], par[1]["nombre"]))

    return [c for _, c in candidatos[:maximo]]


def habilidad(nombre: str) -> dict[str, Any] | None:
    """El contenido de una habilidad (SKILL.md) y la lista de sus anexos."""
    limpio = _clave(nombre)

    for entrada in indice()["habilidades"]:
        if _clave(entrada["nombre"]) == limpio:
            manifiesto = Path(entrada["archivo"])
            datos, cuerpo = _frontmatter(_leer(manifiesto))
            anexos = [
                str(p.relative_to(manifiesto.parent))
                for p in manifiesto.parent.rglob("*")
                if p.is_file() and p != manifiesto
            ]

            return {
                "nombre": entrada["nombre"],
                "descripcion": datos.get("description", ""),
                "contenido": cuerpo,
                "carpeta": str(manifiesto.parent),
                "anexos": anexos[:40],
            }

    return None


def anexo(nombre_habilidad: str, relativo: str) -> str:
    """Un archivo de apoyo de una habilidad (referencias, ejemplos)."""
    h = habilidad(nombre_habilidad)

    if h is None:
        return ""

    archivo = (Path(h["carpeta"]) / relativo).resolve()

    if (
        not str(archivo).startswith(str(Path(h["carpeta"]).resolve()))
        or not archivo.is_file()
    ):
        return ""

    return _leer(archivo)[:20000]


def especialista(nombre: str) -> dict[str, Any] | None:
    """La persona de un especialista: su guion, sus herramientas y su modelo."""
    limpio = _clave(nombre)

    for entrada in indice()["especialistas"]:
        if _clave(entrada["nombre"]) == limpio:
            datos, cuerpo = _frontmatter(_leer(Path(entrada["archivo"])))

            return {
                "nombre": entrada["nombre"],
                "descripcion": datos.get("description", ""),
                "herramientas": [
                    h.strip() for h in datos.get("tools", "").split(",") if h.strip()
                ],
                "modelo": datos.get("model", ""),
                "guion": cuerpo,
            }

    return None


def reglas(lenguaje: str = "common") -> list[dict[str, str]]:
    limpio = sin_adornos(lenguaje)
    salida = []

    for entrada in indice()["reglas"]:
        carpeta = entrada["nombre"].split("/", 1)[0]

        if carpeta == limpio or (limpio in ("todas", "all") and carpeta):
            salida.append(
                {
                    "nombre": entrada["nombre"],
                    "contenido": _leer(Path(entrada["archivo"])),
                }
            )

    return salida


def reglas_para(raiz: Path) -> list[str]:
    """Las carpetas de reglas que aplican a un repositorio, por lo que hay en él."""
    aplican = ["common"]
    pistas = {
        "python": ("pyproject.toml", "requirements.txt", "setup.py"),
        "typescript": ("tsconfig.json",),
        "react": ("next.config.js", "next.config.mjs", "next.config.ts"),
        "golang": ("go.mod",),
        "rust": ("Cargo.toml",),
        "java": ("pom.xml", "build.gradle"),
        "kotlin": ("build.gradle.kts",),
        "php": ("composer.json",),
        "swift": ("Package.swift",),
        "ruby": ("Gemfile",),
        "dart": ("pubspec.yaml",),
    }

    for lenguaje, archivos in pistas.items():
        if any((raiz / a).exists() for a in archivos):
            aplican.append(lenguaje)

    if (raiz / "package.json").exists() and "typescript" not in aplican:
        aplican.append("typescript")

    return aplican


def estado() -> dict[str, Any]:
    base = ruta()
    origen: dict[str, Any] = {}

    try:
        origen = json.loads((base / "origen.json").read_text(encoding="utf-8"))

    except (OSError, ValueError):
        pass

    return {
        "instalada": instalada(),
        "carpeta": str(base),
        "origen": origen.get("origen", ""),
        "fecha": origen.get("fecha", ""),
        **(cuenta() if instalada() else {}),
    }


def olvidar_indice() -> None:
    global _indice

    _indice = None
