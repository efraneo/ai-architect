"""Las órdenes que los agentes obedecen.

Revisar es la mitad del trabajo. La otra mitad es hacer: formatear, corregir,
actualizar, hacer commit, subir, anotar el changelog, etiquetar, reconstruir el
instalador, correr las pruebas, relanzar la CI. Architect da la orden, el
agente la cumple con sus herramientas y devuelve un informe corto.

Cada tarea dice si cambia algo (archivos, git, la máquina) o solo consulta.
Las que cambian pasan por el permiso de Efraín (cola de aprobaciones); las que
consultan, no.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .herramientas_externas import (
    correr,
    correr_json,
    hay,
    modulo_disponible,
    python_de,
)

Hacer = Callable[[Path, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class Tarea:
    nombre: str
    que: str
    hacer: Hacer
    cambia: bool = True
    argumentos: dict[str, str] = field(default_factory=dict)


# --- utilidades -------------------------------------------------------------------


def _resultado(codigo: int, out: str, err: str, hecho: str) -> dict[str, Any]:
    texto = (out or "") + ("\n" + err if err else "")

    return {
        "ok": codigo == 0,
        "hecho": hecho,
        "salida": texto.strip()[-1500:],
    }


def _objetivos(raiz: Path) -> list[str]:
    from .calidad_agent import _paquete_principal

    paquete = _paquete_principal(raiz)
    objetivos = [paquete] if paquete else ["."]

    if paquete and (raiz / "tests").is_dir():
        objetivos.append("tests")

    return objetivos


def _version_de(raiz: Path) -> str:
    from .release_agent import _version_declarada

    return _version_declarada(raiz)


# --- calidad ------------------------------------------------------------------------


def _formatear(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    if not modulo_disponible(raiz, "black"):
        return {"ok": False, "hecho": "no hay black en el proyecto (pip install black)"}

    objetivos = [str(args["ruta"])] if args.get("ruta") else _objetivos(raiz)
    codigo, out, err = correr(
        [python_de(raiz), "-m", "black", "-q", *objetivos], raiz, 300
    )

    return _resultado(codigo, out, err, "formateado con black: " + ", ".join(objetivos))


def _corregir_lint(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    if not modulo_disponible(raiz, "ruff"):
        return {"ok": False, "hecho": "no hay ruff en el proyecto (pip install ruff)"}

    objetivos = [str(args["ruta"])] if args.get("ruta") else _objetivos(raiz)
    orden = [python_de(raiz), "-m", "ruff", "check", "--fix", *objetivos]

    if args.get("solo_errores"):
        orden[4:4] = ["--select", "F,B,PLE"]

    codigo, out, err = correr(orden, raiz, 300)

    return _resultado(codigo, out, err, "ruff --fix sobre " + ", ".join(objetivos))


def _verificar(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    from .calidad_agent import CalidadAgent

    informe = CalidadAgent().review(str(raiz))
    partes = {k: informe[k] for k in ("black", "ruff", "mypy") if k in informe}
    ok = all(v.get("ok") for v in partes.values()) if partes else False

    return {
        "ok": ok,
        "hecho": "verificado formato, lint y tipos",
        "resultado": partes,
        "hallazgos": len(informe.get("findings") or []),
    }


# --- dependencias -----------------------------------------------------------------


def _instalar_paquete(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    from ai_architect import instalar

    nombre = str(args.get("paquete", "")).strip()

    if not nombre:
        return {"ok": False, "hecho": "falta el nombre del paquete"}

    salida = instalar.paquete(nombre, raiz / "requirements.txt")

    return {
        "ok": bool(salida.get("ok")),
        "hecho": (
            f"instalado {nombre}" if salida.get("ok") else str(salida.get("error"))
        ),
        "requirements": salida.get("requirements", False),
    }


def _actualizar_paquetes(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    nombres = [str(args["paquete"]).strip()] if args.get("paquete") else []

    if not nombres:
        datos = correr_json(
            [
                python_de(raiz),
                "-m",
                "pip",
                "list",
                "--outdated",
                "--format",
                "json",
                "--disable-pip-version-check",
            ],
            raiz,
            90,
        )
        nombres = [
            str(d.get("name"))
            for d in (datos if isinstance(datos, list) else [])
            if isinstance(d, dict) and d.get("name")
        ][:15]

    if not nombres:
        return {"ok": True, "hecho": "no hay paquetes desactualizados"}

    codigo, out, err = correr(
        [
            python_de(raiz),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--disable-pip-version-check",
            *nombres,
        ],
        raiz,
        600,
    )

    return _resultado(codigo, out, err, "actualizados: " + ", ".join(nombres))


# --- git ----------------------------------------------------------------------------


def _git(raiz: Path, *partes: str, tiempo: int = 120) -> tuple[int, str, str]:
    return correr(["git", *partes], raiz, tiempo)


def _commit(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    mensaje = str(args.get("mensaje", "")).strip()

    if not mensaje:
        return {"ok": False, "hecho": "falta el mensaje del commit"}

    codigo, out, err = _git(raiz, "add", "-A")

    if codigo != 0:
        return _resultado(codigo, out, err, "git add falló")

    codigo, out, err = _git(raiz, "commit", "-q", "-m", mensaje)

    return _resultado(codigo, out, err, f"commit: {mensaje[:80]}")


def _subir(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    partes = ["push", "-q"]

    if args.get("rama"):
        partes += ["origin", str(args["rama"])]

    codigo, out, err = _git(raiz, *partes, tiempo=300)

    return _resultado(codigo, out, err, "subido a origin")


def _traer(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    codigo, out, err = _git(raiz, "pull", "--ff-only", "-q", tiempo=300)

    return _resultado(codigo, out, err, "traído de origin (solo avance rápido)")


def _rama(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    nombre = str(args.get("nombre", "")).strip()

    if not re.match(r"^[\w./-]+$", nombre):
        return {"ok": False, "hecho": "falta un nombre de rama válido"}

    codigo, out, err = _git(raiz, "checkout", "-q", "-b", nombre)

    return _resultado(codigo, out, err, f"rama {nombre} creada y activa")


# --- publicación --------------------------------------------------------------------


def _commits_desde_etiqueta(raiz: Path) -> list[str]:
    codigo, ultima, _ = _git(raiz, "describe", "--tags", "--abbrev=0")
    rango = f"{ultima.strip()}..HEAD" if codigo == 0 and ultima.strip() else "-20"
    codigo, out, _ = _git(raiz, "log", rango, "--format=%s")

    if codigo != 0:
        return []

    return [ln.strip() for ln in out.splitlines() if ln.strip()][:30]


def _anotar_changelog(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    version = str(args.get("version") or _version_de(raiz) or "").strip()

    if not version:
        return {"ok": False, "hecho": "no sé qué versión anotar (dime la versión)"}

    archivo = raiz / "CHANGELOG.md"
    actual = (
        archivo.read_text(encoding="utf-8") if archivo.is_file() else "# Cambios\n\n"
    )

    if re.search(rf"^##\s*\[?v?{re.escape(version)}\]?", actual, re.M):
        return {"ok": True, "hecho": f"el CHANGELOG ya tiene la versión {version}"}

    notas = [str(n).strip() for n in (args.get("notas") or []) if str(n).strip()]

    if not notas:
        notas = _commits_desde_etiqueta(raiz) or ["cambios de esta versión"]

    seccion = f"## {version} — {date.today():%Y-%m-%d}\n\n" + "".join(
        f"- {n}\n" for n in notas
    )
    cabecera, _, resto = actual.partition("\n## ")
    nuevo = cabecera.rstrip() + "\n\n" + seccion + ("\n## " + resto if resto else "")
    archivo.write_text(
        nuevo if nuevo.endswith("\n") else nuevo + "\n", encoding="utf-8"
    )

    return {
        "ok": True,
        "hecho": f"anotada la versión {version} en CHANGELOG.md ({len(notas)} punto(s))",
    }


def _subir_version(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    nueva = str(args.get("version", "")).strip()

    if not re.match(r"^\d+\.\d+\.\d+$", nueva):
        return {"ok": False, "hecho": "dime la versión nueva, por ejemplo 0.3.0"}

    cambiados: list[str] = []
    patrones = {
        "pyproject.toml": (r'^(version\s*=\s*")([^"]+)(")', re.M),
        "instalador.iss": (r'(#define\s+Version\s+")([^"]+)(")', 0),
    }

    for nombre, (patron, banderas) in patrones.items():
        archivo = raiz / nombre

        if not archivo.is_file():
            continue

        texto = archivo.read_text(encoding="utf-8")
        nuevo, n = re.subn(
            patron, rf"\g<1>{nueva}\g<3>", texto, count=1, flags=banderas
        )

        if n:
            archivo.write_text(nuevo, encoding="utf-8")
            cambiados.append(nombre)

    if not cambiados:
        return {"ok": False, "hecho": "no encontré dónde está declarada la versión"}

    return {"ok": True, "hecho": f"versión {nueva} en " + ", ".join(cambiados)}


# --- empaquetado ----------------------------------------------------------------------


def _reconstruir(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    from ai_architect import autoreparacion

    salida = autoreparacion.reconstruir()

    return {
        "ok": bool(salida.get("ok")),
        "hecho": str(salida.get("informe", "")),
        "instalador": salida.get("instalador", ""),
    }


def _etiquetar(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    version = str(args.get("version") or _version_de(raiz) or "").strip()

    if not version:
        return {"ok": False, "hecho": "no sé qué versión etiquetar"}

    etiqueta = f"v{version}"
    codigo, out, err = _git(raiz, "tag", "-a", etiqueta, "-m", f"Versión {version}")

    if codigo != 0:
        return _resultado(codigo, out, err, f"no pude crear {etiqueta}")

    codigo, out, err = _git(raiz, "push", "-q", "origin", etiqueta, tiempo=300)

    return _resultado(codigo, out, err, f"etiqueta {etiqueta} creada y subida")


# --- pruebas ------------------------------------------------------------------------------


def _correr_pruebas(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    if not modulo_disponible(raiz, "pytest"):
        return {"ok": False, "hecho": "no hay pytest en el proyecto"}

    orden = [python_de(raiz), "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"]

    if args.get("ruta"):
        orden.append(str(args["ruta"]))

    if args.get("filtro"):
        orden += ["-k", str(args["filtro"])]

    codigo, out, err = correr(orden, raiz, 900)
    resumen = next(
        (ln for ln in reversed(out.splitlines()) if "passed" in ln or "failed" in ln),
        "",
    )

    salida = _resultado(codigo, out, err, resumen or "pruebas corridas")
    salida["resumen"] = resumen

    return salida


# --- devops ----------------------------------------------------------------------------


def _ver_ci(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    if not hay("gh"):
        return {"ok": False, "hecho": "no está gh (GitHub CLI) en esta máquina"}

    datos = correr_json(
        [
            "gh",
            "run",
            "list",
            "--limit",
            "5",
            "--json",
            "databaseId,status,conclusion,displayTitle,createdAt",
        ],
        raiz,
        60,
    )

    if not isinstance(datos, list):
        return {
            "ok": False,
            "hecho": "gh no respondió (¿hay remoto en GitHub y sesión?)",
        }

    return {
        "ok": True,
        "hecho": f"{len(datos)} corrida(s) recientes de la CI",
        "corridas": [
            {
                "id": d.get("databaseId"),
                "estado": d.get("conclusion") or d.get("status"),
                "titulo": str(d.get("displayTitle", ""))[:80],
            }
            for d in datos
            if isinstance(d, dict)
        ],
    }


def _relanzar_ci(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    if not hay("gh"):
        return {"ok": False, "hecho": "no está gh (GitHub CLI) en esta máquina"}

    id_ = str(args.get("id", "")).strip()

    if not id_:
        vista = _ver_ci(raiz, {})
        fallidas = [
            c for c in vista.get("corridas", []) if c.get("estado") == "failure"
        ]

        if not fallidas:
            return {"ok": True, "hecho": "no hay ninguna corrida fallida que relanzar"}

        id_ = str(fallidas[0]["id"])

    codigo, out, err = correr(["gh", "run", "rerun", id_, "--failed"], raiz, 60)

    return _resultado(codigo, out, err, f"relanzada la corrida {id_}")


# --- seguridad ------------------------------------------------------------------------------


def _proteger_secretos(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    archivo = raiz / ".gitignore"
    actual = archivo.read_text(encoding="utf-8") if archivo.is_file() else ""
    lineas = {ln.strip() for ln in actual.splitlines()}
    faltan = [
        p for p in (".env", ".env.*", "*.env", "*.pem", "*.key") if p not in lineas
    ]

    if not faltan:
        return {"ok": True, "hecho": "el .gitignore ya protege los secretos"}

    nuevo = actual.rstrip() + ("\n\n" if actual.strip() else "") + "# secretos\n"
    nuevo += "".join(f"{p}\n" for p in faltan)
    archivo.write_text(nuevo, encoding="utf-8")

    return {"ok": True, "hecho": "añadido al .gitignore: " + ", ".join(faltan)}


# --- voz y canales ------------------------------------------------------------------------


def _instalar_ventana(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    from ai_architect import instalar

    salida = instalar.paquete("pywebview", raiz / "requirements.txt")

    return {
        "ok": bool(salida.get("ok")),
        "hecho": (
            "pywebview instalado: ya hay ventana flotante (reinicia Architect)"
            if salida.get("ok")
            else str(salida.get("error"))
        ),
    }


def _probar_voz(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    from ai_architect.voz import hablar

    texto = str(args.get("texto") or "Probando la voz de Architect.")
    salida = hablar.hablar(texto)

    return {
        "ok": bool(salida.get("hablado")),
        "hecho": f"voz probada con «{texto[:60]}»",
        "detalle": {k: v for k, v in salida.items() if k != "audio"},
    }


def _configurar_canal(raiz: Path, args: dict[str, Any]) -> dict[str, Any]:
    from ai_architect.canales import asistente

    canal = str(args.get("canal", "")).strip().lower()

    if canal not in ("telegram", "correo", "whatsapp", "celular"):
        return {
            "ok": False,
            "hecho": "dime el canal: telegram, correo, whatsapp o celular",
        }

    salida = asistente.empezar(canal)

    return {"ok": True, "hecho": str(salida.get("respuesta") or "configurando")}


# --- el catálogo -------------------------------------------------------------------------

CATALOGO: dict[str, dict[str, Tarea]] = {
    "calidad": {
        "formatear": Tarea(
            "formatear",
            "formatea el código con black",
            _formatear,
            True,
            {"ruta": "opcional"},
        ),
        "corregir": Tarea(
            "corregir",
            "corrige con ruff --fix lo que sabe corregir solo",
            _corregir_lint,
            True,
            {"ruta": "opcional"},
        ),
        "verificar": Tarea(
            "verificar", "black --check, ruff y mypy, sin tocar nada", _verificar, False
        ),
    },
    "errores": {
        "corregir": Tarea(
            "corregir",
            "corrige con ruff --fix los errores reales (F, B, PLE)",
            lambda raiz, args: _corregir_lint(raiz, {**args, "solo_errores": True}),
            True,
            {"ruta": "opcional"},
        ),
    },
    "dependencias": {
        "instalar": Tarea(
            "instalar",
            "pip install del paquete y lo anota en requirements.txt",
            _instalar_paquete,
            True,
            {"paquete": "nombre en PyPI"},
        ),
        "actualizar": Tarea(
            "actualizar",
            "pip install --upgrade de un paquete o de todos los desactualizados",
            _actualizar_paquetes,
            True,
            {"paquete": "opcional; sin paquete actualiza todos"},
        ),
    },
    "git": {
        "commit": Tarea(
            "commit",
            "git add -A y commit con el mensaje",
            _commit,
            True,
            {"mensaje": "texto"},
        ),
        "subir": Tarea(
            "subir", "git push a origin", _subir, True, {"rama": "opcional"}
        ),
        "traer": Tarea("traer", "git pull --ff-only", _traer, True),
        "rama": Tarea(
            "rama", "crea una rama y se pasa a ella", _rama, True, {"nombre": "texto"}
        ),
    },
    "publicacion": {
        "anotar_changelog": Tarea(
            "anotar_changelog",
            "añade la sección de la versión al CHANGELOG con los commits desde la última etiqueta",
            _anotar_changelog,
            True,
            {"version": "opcional", "notas": "lista opcional de puntos"},
        ),
        "subir_version": Tarea(
            "subir_version",
            "cambia la versión en pyproject.toml e instalador.iss",
            _subir_version,
            True,
            {"version": "x.y.z"},
        ),
    },
    "empaquetado": {
        "reconstruir": Tarea(
            "reconstruir",
            "reconstruye el instalador (empaquetar.cmd)",
            _reconstruir,
            True,
        ),
        "etiquetar": Tarea(
            "etiquetar",
            "crea la etiqueta v<version> en git y la sube",
            _etiquetar,
            True,
            {"version": "opcional"},
        ),
    },
    "pruebas": {
        "correr": Tarea(
            "correr",
            "corre pytest (todo, una ruta o un filtro -k)",
            _correr_pruebas,
            False,
            {"ruta": "opcional", "filtro": "opcional"},
        ),
    },
    "devops": {
        "ver_ci": Tarea(
            "ver_ci", "las últimas corridas de GitHub Actions", _ver_ci, False
        ),
        "relanzar_ci": Tarea(
            "relanzar_ci",
            "relanza los trabajos fallidos de la última corrida (o de un id)",
            _relanzar_ci,
            True,
            {"id": "opcional"},
        ),
    },
    "seguridad": {
        "proteger_secretos": Tarea(
            "proteger_secretos",
            "asegura que .env y llaves estén en .gitignore",
            _proteger_secretos,
            True,
        ),
    },
    "voz": {
        "instalar_ventana": Tarea(
            "instalar_ventana",
            "instala pywebview para la ventana flotante",
            _instalar_ventana,
        ),
        "probar_voz": Tarea(
            "probar_voz",
            "dice una frase con la voz actual",
            _probar_voz,
            False,
            {"texto": "opcional"},
        ),
        "instalar_huella": Tarea(
            "instalar_huella",
            "instala resemblyzer para reconocer tu voz (huella de voz)",
            lambda raiz, args: _instalar_paquete(raiz, {"paquete": "resemblyzer"}),
        ),
        "instalar_oido_local": Tarea(
            "instalar_oido_local",
            "instala faster-whisper para oír sin red (ARCHITECT_OIDO=local)",
            lambda raiz, args: _instalar_paquete(raiz, {"paquete": "faster-whisper"}),
        ),
        "configurar_canal": Tarea(
            "configurar_canal",
            "empieza la configuración guiada de un canal",
            _configurar_canal,
            True,
            {"canal": "telegram | correo | whatsapp | celular"},
        ),
    },
}


def tareas_de(clave: str) -> dict[str, Tarea]:
    return CATALOGO.get(clave, {})


def ejecutar(clave: str, tarea: str, project: str, **args: Any) -> dict[str, Any]:
    """Un agente cumple una orden. Devuelve siempre un dict con ``ok`` y ``hecho``."""
    disponibles = tareas_de(clave)

    if tarea not in disponibles:
        opciones = ", ".join(disponibles) or "ninguna"

        return {
            "ok": False,
            "hecho": f"el agente {clave} no sabe «{tarea}»; sabe: {opciones}",
        }

    raiz = Path(project).resolve()

    try:
        salida = disponibles[tarea].hacer(raiz, dict(args))

    except Exception as e:  # noqa: BLE001 - la orden falló, se cuenta
        return {"ok": False, "hecho": f"{clave}.{tarea} falló: {e}"}

    salida.setdefault("ok", False)
    salida.setdefault("hecho", "")

    return salida


def catalogo_en_texto(solo_cambian: bool | None = None) -> str:
    """El catálogo, en una línea por agente, para la descripción de la herramienta."""
    lineas = []

    for clave, tareas in CATALOGO.items():
        elegidas = [
            t
            for t in tareas.values()
            if solo_cambian is None or t.cambia == solo_cambian
        ]

        if elegidas:
            lineas.append(
                f"{clave}: "
                + "; ".join(
                    t.nombre
                    + (
                        " ("
                        + ", ".join(f"{a}: {d}" for a, d in t.argumentos.items())
                        + ")"
                        if t.argumentos
                        else ""
                    )
                    for t in elegidas
                )
            )

    return "\n".join(lineas)
