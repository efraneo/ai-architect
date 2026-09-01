"""
=========================================================
Pide

Una frase, y el arquitecto elige qué hacer.
=========================================================

El arquitecto ya tenía las herramientas —los ocho comandos— pero no había
quien las escogiera. ``improve --instruction "..."`` acepta una frase, pero
solo sabe hacer una cosa: generar un parche. No responde preguntas ni decide
qué comando toca.

Esto es esa pieza: la frase va al modelo, el modelo dice **cuál de los ocho
comandos** resuelve lo que se pide, y se ejecuta.

Dos reglas que no se negocian:

1. **El modelo elige de una lista cerrada.** No puede inventarse un comando
   ni ejecutar nada que no esté en la tabla del CLI. Si devuelve algo que no
   existe, se para y se dice.
2. **Lo que modifica archivos pide permiso.** Los comandos de solo lectura
   se ejecutan directamente; los que tocan el repositorio se muestran y
   esperan un ``--si``. Adivinar que una frase autoriza a modificar código
   es justo lo que no hay que hacer.

Una sola llamada al proveedor: la de interpretar. La explicación del
resultado se arma aquí, que sale gratis y no se inventa nada.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ai_architect.core import perfil

# Comandos que tocan el repositorio del usuario. No se ejecutan sin permiso
# explícito, por muy claro que parezca lo que pidió.
MODIFICAN = {"execute"}

# Banderas que convierten un comando inofensivo en uno que escribe.
BANDERAS_QUE_ESCRIBEN = ("apply", "write")

INSTRUCCIONES = """Eres el despachador de QUANT AI Architect.

El usuario escribe una frase en español. Tu único trabajo es decir cuál de
estos comandos la resuelve, y con qué argumentos.

COMANDOS DISPONIBLES
{catalogo}

ARGUMENTOS
  project        ruta del repositorio (por defecto ".")
  instruction    para improve: qué mejora se pide, en una frase
  file           para improve: archivo concreto a modificar, si se nombra
  apply          para improve/auto: true SOLO si el usuario pide aplicar,
                 arreglar, corregir o cambiar el código de verdad
  instructions   para auto: lista de frases, la más importante primero
  ai             para agents: true solo si pide análisis con IA
  version_name   para changelog: nombre de la versión, si lo dice
  write          para changelog: true solo si pide escribir el archivo
  patch          para execute: ruta del parche
  dry_run        para execute: true si pide validar sin aplicar

REGLAS
- Responde SOLO con un objeto JSON. Nada más, sin markdown, sin explicación.
- Usa exactamente uno de los comandos de la lista.
- "puntuación", "nota", "score", "cuánto saca", "qué tal está el código"
  -> "review" (es el único que puntúa).
- "cómo va", "qué problemas hay", "revísalo", "hallazgos", "seguridad"
  -> "agents".
- "cuántos archivos", "cuántas funciones", "estructura", "complejidad media"
  -> "analyze".
- "arregla", "mejora", "cambia", "añade", "extrae" -> "improve" con
  instruction en español, copiando lo que pidió.
- "está todo bien configurado", "funciona", "tengo la clave" -> "doctor".
- Pon apply/write en true SOLO si la frase lo pide de verdad. "dime",
  "muéstrame" y "revisa" NO lo piden; "arregla", "aplica" y "hazlo" sí.
- Si no entiendes qué quiere, responde {{"comando": "", "motivo": "..."}}.

FORMATO
{{"comando": "agents", "project": ".", "razon": "pregunta por el estado"}}

LA FRASE
{frase}
"""


def run(
    project: str,
    frase: str,
    si: bool = False,
    soy: str = "",
    decir: bool = False,
    cara: bool = False,
    engine: Any = None,
) -> dict:
    """Interpreta la frase y ejecuta el comando que corresponda.

    Parameters
    ----------
    project:
        Repositorio por defecto, si la frase no nombra otro.
    frase:
        Lo que pidió el usuario, tal cual.
    si:
        Autoriza los comandos que modifican archivos.
    engine:
        Proveedor inyectable, para que las pruebas no llamen a nadie.
    """
    if soy.strip():
        datos = perfil.configurar(soy)

        return {
            "success": True,
            "executed": False,
            "profile": datos,
            "explanation": "\n\n".join(
                [
                    f"{perfil.encabezar()} Encantado.",
                    f"A partir de ahora te llamo {datos['tratamiento']}. "
                    f"Me hizo {datos['creador']}.",
                    'Pídeme lo que quieras: architect pide "cómo está el proyecto"',
                ]
            ),
        }

    repositorio = Path(project).resolve()

    if not repositorio.exists():
        return _error(f"No existe el repositorio: {repositorio}")

    if not frase.strip():
        return _error("No dijiste qué quieres que haga.")

    # La primera vez no sabe a quién le habla. Se pregunta una sola vez y se
    # recuerda: preguntarlo cada sesión sería peor que no preguntarlo.
    if not perfil.esta_configurado():
        return {
            "success": True,
            "executed": False,
            "needs_profile": True,
            "explanation": "\n\n".join(
                [
                    f"{perfil.saludo()}. Es la primera vez que hablamos.",
                    "¿Cómo quieres que te llame? Dímelo así:\n"
                    '    architect pide --soy "Eathan"',
                    f"Me hizo {perfil.quien_te_hizo()}.",
                ]
            ),
        }

    catalogo, tabla = _catalogo()

    try:
        cruda = _preguntar(engine, catalogo, frase)

    except Exception as e:  # noqa: BLE001 - un proveedor caído no revienta
        return _error(f"el proveedor falló: {e}")

    intencion = _leer_json(cruda)

    if intencion is None:
        return _error(
            "no entendí la respuesta del modelo",
            crudo=cruda[:400],
        )

    nombre = str(intencion.get("comando", "")).strip()

    if not nombre:
        return _error(
            str(intencion.get("motivo") or "no supe qué comando usar"),
            frase=frase,
        )

    if nombre not in tabla:
        # El modelo se inventó un comando. Se para aquí: ejecutar algo que no
        # está en la tabla es exactamente lo que no puede pasar.
        return _error(
            f"el modelo pidió un comando que no existe: {nombre}",
            disponibles=sorted(tabla),
        )

    comando = tabla[nombre]

    args = _argumentos(intencion, str(repositorio))

    escribe = nombre in MODIFICAN or any(
        getattr(args, bandera, False) for bandera in BANDERAS_QUE_ESCRIBEN
    )

    orden = _como_se_escribe(nombre, args)

    if escribe and not si:
        return {
            "success": True,
            "executed": False,
            "command": nombre,
            "would_run": orden,
            "reason": (
                "esto modifica archivos de tu repositorio. "
                "Repite con --si para que lo haga."
            ),
            "explanation": _con_trato(
                f"Entendí que quieres: {orden}\n"
                "No lo ejecuto porque toca tus archivos. Añade --si si es eso."
            ),
        }

    for bandera, mensaje in comando.requiere:
        if not getattr(args, bandera, None):
            return _error(f"falta un dato para {nombre}: {mensaje}")

    try:
        resultado = comando.ejecutar(args)

    except Exception as e:  # noqa: BLE001 - el comando falla, `pide` informa
        return _error(f"{nombre} falló: {e}", command=nombre)

    respuesta = {
        "success": True,
        "executed": True,
        "command": nombre,
        "ran": orden,
        "explanation": _con_trato(explicar(nombre, resultado)),
        "result": resultado,
    }

    return _decir_si_toca(respuesta, decir, cara)


def _decir_si_toca(
    respuesta: dict[str, Any],
    decir: bool,
    cara: bool = False,
) -> dict[str, Any]:
    """Lee la respuesta en alto, si se pidió.

    Que no haya voz no puede impedir que el comando sirva: la respuesta ya
    está escrita en la pantalla. Por eso el fallo se anota y no se lanza.
    """
    if not decir and not cara:
        return respuesta

    texto = str(respuesta.get("explanation", ""))

    # Con la cara el audio no se reproduce aquí: lo lanza el avatar, que
    # necesita saber cuánto dura antes de empezar para mover la boca
    # justo ese rato y no un segundo de más.
    if cara:
        from ai_architect.commands import avatar

        respuesta["face"] = avatar.run(decir=texto if decir else "")

        return respuesta

    from ai_architect.voz.hablar import hablar

    respuesta["spoken"] = hablar(texto)

    return respuesta


def _con_trato(cuerpo: str) -> str:
    """La respuesta, entre el saludo y la despedida del momento del día.

    Es lo que separa una herramienta de algo que se siente tuyo: que sepa a
    quién le habla y qué hora es.
    """
    return "\n\n".join([perfil.encabezar(), cuerpo, perfil.despedir()])


def explicar(nombre: str, resultado: Any) -> str:
    """El resultado, en una frase que se entienda.

    Se arma aquí y no con otra llamada al modelo: los resultados son
    diccionarios que controlamos, así que explicarlos no necesita IA — y una
    segunda llamada duplicaría el coste para inventar lo que ya sabemos.
    """
    if not isinstance(resultado, dict):
        return str(resultado)

    if not resultado.get("success", True):
        return f"No salió: {resultado.get('error', 'sin motivo')}"

    if nombre == "doctor":
        estado = resultado.get("status", "?")
        partes = [
            f"{clave}: {(valor or {}).get('status', '?')}"
            for clave, valor in (resultado.get("components") or {}).items()
            if isinstance(valor, dict)
        ]
        return f"El entorno está {estado}. " + ", ".join(partes)

    if nombre == "agents":
        veredicto = resultado.get("verdict") or {}
        con = veredicto.get("agents_with_findings") or []
        return (
            f"{veredicto.get('total_agents', 0)} agentes revisaron el proyecto. "
            f"{resultado.get('total_findings', 0)} hallazgos"
            + (f", en: {', '.join(con)}." if con else ", ninguno.")
        )

    if nombre == "review":
        return (
            f"Puntuación {resultado.get('score')}, "
            f"{resultado.get('total_issues', 0)} incidencias. "
            + ("Aprobado." if resultado.get("approved") else "No aprobado.")
        )

    if nombre == "analyze":
        resumen = resultado.get("summary") or {}
        return (
            f"{resumen.get('python_files', 0)} archivos Python, "
            f"{resumen.get('total_functions', 0)} funciones, "
            f"complejidad media {resumen.get('average_complexity', 0)}."
        )

    if nombre == "improve":
        return _explicar_mejora(resultado)

    if nombre == "auto":
        return (
            f"{resultado.get('executed', 0)} de {resultado.get('total_tasks', 0)} "
            f"tareas ejecutadas, {resultado.get('approved', 0)} aprobadas."
        )

    if nombre == "changelog":
        return (
            f"Versión {resultado.get('version')}: "
            f"{resultado.get('total_changes', 0)} cambios desde "
            f"{resultado.get('since')}. "
            + (
                "Escrito en CHANGELOG.md."
                if resultado.get("written")
                else "No escrito."
            )
        )

    return "Hecho."


def _explicar_mejora(resultado: dict[str, Any]) -> str:
    """Lo de `improve` merece detalle: dice si tus archivos cambiaron."""
    arbol = {
        "untouched": "No toqué ningún archivo tuyo.",
        "modified": "El cambio quedó aplicado. Revísalo.",
        "restored": "Lo apliqué, rompía las pruebas, y lo deshice.",
        "dirty": "ATENCIÓN: rompía las pruebas y no se pudo deshacer.",
    }.get(str(resultado.get("working_tree", "")), "")

    decision = resultado.get("decision") or {}

    return (
        f"Parche de {resultado.get('files', 0)} archivo(s). "
        f"Decisión: {decision.get('decision', '?')} "
        f"(score {(decision.get('metrics') or {}).get('score', '?')}). " + arbol
    )


def _catalogo() -> tuple[str, dict[str, Any]]:
    """La lista de comandos, tomada de la tabla del CLI.

    Se importa aquí dentro a propósito: el CLI importa este módulo, y hacerlo
    arriba sería un ciclo. Y se toma de allí para que no haya dos listas que
    puedan desincronizarse.
    """
    from ai_architect.cli import COMANDOS, POR_NOMBRE

    lineas = [f"  {c.nombre}: {c.ayuda}" for c in COMANDOS]

    return "\n".join(lineas), POR_NOMBRE


def _preguntar(engine: Any, catalogo: str, frase: str) -> str:
    proveedor = engine

    if proveedor is None:
        from ai_architect.providers.provider_manager import ProviderManager

        proveedor = ProviderManager()

    return str(
        proveedor.generate(
            INSTRUCCIONES.format(catalogo=catalogo, frase=frase),
        )
    )


def _leer_json(texto: str) -> dict[str, Any] | None:
    """El JSON de la respuesta, aunque venga envuelto en explicación."""
    if not texto:
        return None

    try:
        return dict(json.loads(texto))

    except (ValueError, TypeError):
        # No vino limpio; abajo se intenta rescatarlo de dentro del texto.
        pass

    # Un modelo puede envolverlo en ```json o rodearlo de texto.
    coincidencia = re.search(r"\{.*\}", texto, re.DOTALL)

    if coincidencia is None:
        return None

    try:
        return dict(json.loads(coincidencia.group(0)))

    except (ValueError, TypeError):
        return None


def _argumentos(intencion: dict[str, Any], repositorio: str) -> SimpleNamespace:
    """Los argumentos que espera la tabla del CLI, con valores por defecto."""
    instrucciones = intencion.get("instructions")

    return SimpleNamespace(
        project=str(intencion.get("project") or repositorio),
        file=intencion.get("file") or None,
        instruction=str(intencion.get("instruction") or "Improve code quality"),
        instructions=list(instrucciones) if isinstance(instrucciones, list) else None,
        apply=bool(intencion.get("apply", False)),
        ai=bool(intencion.get("ai", False)),
        version_name=str(intencion.get("version_name") or ""),
        write=bool(intencion.get("write", False)),
        since=intencion.get("since") or None,
        patch=intencion.get("patch") or None,
        dry_run=bool(intencion.get("dry_run", False)),
        json=False,
    )


def _como_se_escribe(nombre: str, args: SimpleNamespace) -> str:
    """El comando equivalente, para que se vea qué se va a ejecutar."""
    partes = [f"architect {nombre} {args.project}"]

    if args.file:
        partes.append(f"--file {args.file}")

    if nombre == "improve" and args.instruction:
        partes.append(f'--instruction "{args.instruction}"')

    if args.instructions:
        partes.append("--instructions " + " ".join(f'"{i}"' for i in args.instructions))

    if args.patch:
        partes.append(f"--patch {args.patch}")

    for bandera in ("apply", "ai", "write", "dry_run"):
        if getattr(args, bandera, False):
            partes.append(f"--{bandera.replace('_', '-')}")

    return " ".join(partes)


def _error(mensaje: str, **extra: Any) -> dict[str, Any]:
    return {
        "success": False,
        "executed": False,
        "error": mensaje,
        "explanation": mensaje,
        **extra,
    }
