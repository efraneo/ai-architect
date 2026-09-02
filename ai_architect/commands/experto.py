"""
=========================================================
Experto

Quién contesta cada pregunta.
=========================================================

El arquitecto contestaba él mismo a todo, con el mismo modelo rápido que
usa para elegir comando. Sirve para despachar; no para responder de un
tema como quien sabe del tema.

Esto le pone un director delante: mira lo que se pide, **decide a qué
especialista le toca** y se lo encarga. Si la pregunta tiene varias
partes, reparte y los consulta a la vez.

**Dos clases de especialista, y la diferencia importa.**

- Los del **proyecto** son los agentes que ya existen —seguridad,
  rendimiento, pruebas, dependencias, documentación— y de verdad leen tu
  código. Cuando la pregunta va del repositorio, contesta quien lo ha
  mirado, no quien lo imagina.
- Los de **fuera** son papeles que adopta el modelo: biología, derecho,
  historia, matemáticas. No leen nada; saben. Y se dice cuál contestó, que
  no es lo mismo oír "creo que sí" que "te lo dice el de seguridad".

**Por qué en paralelo.** Está medido en este mismo repositorio: hilos con
los agentes estáticos van 2,14x más *lentos* —su trabajo está repetido, no
repartido— pero con los que esperan al proveedor van 5x más rápidos.
Consultar a tres especialistas cuesta casi lo mismo que consultar a uno,
así que se reutiliza el ``TaskDispatcher`` que ya estaba escrito para eso.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ai_architect.core import perfil
from ai_architect.core.texto import sin_adornos
from ai_architect.swarm.task_dispatcher import TaskDispatcher

# Los agentes del proyecto que sí leen el código, con lo que cubre cada uno.
# La clave es como se nombra hablando.
DEL_PROYECTO = {
    "seguridad": "secretos, contraseñas, inyección, permisos, dependencias con fallos",
    "rendimiento": "lentitud, bucles caros, consultas repetidas, memoria",
    "pruebas": "cobertura, casos sin probar, pruebas frágiles",
    "dependencias": "librerías, versiones, licencias, lo que sobra",
    "documentacion": "docstrings, README, lo que no está explicado",
    "arquitectura": "estructura, acoplamiento, módulos, complejidad",
}

# Cuántos se consultan como mucho a la vez. Más que esto es gastar por
# gastar: a partir del tercero las respuestas empiezan a repetirse.
MAXIMO = 3

DIRECCION = """Eres el director del equipo. {trato} ha pedido esto:

    {peticion}

Decide quién debe contestarle. Tienes dos clases de especialista:

DEL PROYECTO (leen el código del repositorio de verdad)
{agentes}

DE FUERA (cualquier campo del saber: biología, derecho, historia,
matemáticas, medicina, cocina, finanzas, lo que haga falta)
  Nómbralo por su especialidad, en español y en dos o tres palabras.

Devuelve SOLO un objeto JSON:

{{"especialistas": [
    {{"quien": "seguridad", "propio": true, "encargo": "qué le pides"}},
    {{"quien": "biología celular", "propio": false, "encargo": "..."}}
]}}

REGLAS
- Uno normalmente. Dos o tres solo si la pregunta tiene partes distintas
  que necesitan saberes distintos. Nunca más de {maximo}.
- `propio: true` solo para los de la lista de arriba, y solo cuando la
  pregunta va del repositorio.
- `encargo` es lo que le dirías a esa persona: concreto y completo.
- Si es charla o cortesía, un solo especialista de fuera llamado
  "conversación".
"""

CONSULTA = """Eres {quien}, y de eso sabes de verdad. {trato} te pregunta:

    {encargo}

Contesta como el experto que eres: con criterio, con las cifras o los
nombres que hagan falta, y sin rodeos. Si algo no se sabe con certeza, dilo
y di hasta dónde llegas — eso también es saber. Nunca mandes a nadie a
buscarlo en otro sitio.

Devuelve SOLO un objeto JSON:

{{"resumen": "una o dos frases, que se van a leer en voz alta",
  "respuesta": "lo que le dirías por escrito, tan largo como haga falta"}}

El `resumen` es lo único que se oirá: nada de listas, rutas ni símbolos.

Y tiene que decir **qué**, con el dato concreto: qué has encontrado, qué
cifra sale, qué harías. "Hay problemas que deben corregirse" no dice nada
— eso ya lo sabía antes de preguntar. "Hay dos contraseñas escritas en el
código, en config y en el arranque" sí.
"""


def responder(
    peticion: str,
    project: str = ".",
    engine: Any = None,
) -> dict[str, Any]:
    """Dirige la pregunta al especialista que toque y devuelve su respuesta."""
    if not peticion.strip():
        return {"success": False, "error": "no dijiste qué quieres saber"}

    proveedor = _proveedor(engine)

    try:
        plan = _dirigir(proveedor, peticion, engine)

    except Exception as e:  # noqa: BLE001 - un proveedor caído no revienta
        return {"success": False, "error": f"el proveedor falló: {e}"}

    if not plan:
        return {"success": False, "error": "no supe a quién preguntárselo"}

    # A la vez: lo que se tarda es esperar al proveedor, y esperar tres
    # veces en paralelo cuesta lo mismo que esperar una.
    reparto = TaskDispatcher().dispatch(
        plan,
        lambda encargo: _consultar(proveedor, encargo, project, engine),
        nombre=lambda encargo: str(encargo.get("quien", "?")),
    )

    contestaron = [
        (quien, salida)
        for quien, salida in _ordenar(reparto, plan)
        if isinstance(salida, dict) and salida.get("resumen")
    ]

    if not contestaron:
        return {"success": False, "error": "ninguno supo contestar"}

    return {
        "success": True,
        "executed": True,
        "specialists": [quien for quien, _ in contestaron],
        "explanation": _hablado(contestaron),
        "written": _escrito(contestaron),
        "panel": {
            "tipo": "texto",
            "titulo": _titulo(contestaron),
            "cuerpo": _escrito(contestaron),
        },
    }


# --- Dirigir ----------------------------------------------------------------


def es_charla(quien: str) -> bool:
    """Si ese "especialista" es el comodin de cuando no hay nada que consultar.

    Se compara sin tildes ni mayusculas porque el modelo escribe el nombre
    como le parece —"conversación", "Conversacion", "conversacion"— y una
    comparacion literal deja pasar la mitad.
    """
    return sin_adornos(quien) == "conversacion"


def _dirigir(
    proveedor: Any,
    peticion: str,
    engine: Any = None,
) -> list[dict[str, Any]]:
    catalogo = "\n".join(
        f"  {nombre}: {cubre}" for nombre, cubre in DEL_PROYECTO.items()
    )

    from ai_architect.commands.pide import MODELOS_RAPIDOS

    crudo = _hablar_con(
        proveedor,
        DIRECCION.format(
            trato=perfil.como_llamarte(),
            peticion=peticion,
            agentes=catalogo,
            maximo=MAXIMO,
        ),
        engine,
        MODELOS_RAPIDOS[-1],
    )

    leido = _json(crudo)

    encargos = (leido or {}).get("especialistas") or []

    limpios: list[dict[str, Any]] = []

    for encargo in encargos[:MAXIMO]:
        quien = str(encargo.get("quien") or "").strip()

        if not quien:
            continue

        limpios.append(
            {
                "quien": quien,
                # `propio` solo vale si de verdad es uno de los nuestros: el
                # modelo puede marcar como agente del proyecto a alguien que
                # no existe, y entonces se prometería una lectura del código
                # que nadie ha hecho.
                "propio": bool(encargo.get("propio")) and quien.lower() in DEL_PROYECTO,
                "encargo": str(encargo.get("encargo") or peticion),
            }
        )

    # `conversación` es el comodín de cuando no hay nada que consultar: al
    # lado de un especialista de verdad solo estorba. Se vio en uso —a
    # "qué riesgos de seguridad tengo" contestaron el agente de seguridad
    # y, detrás, una definición de diccionario de la palabra "riesgo"—.
    con_oficio = [e for e in limpios if not es_charla(e["quien"])]

    if con_oficio:
        return con_oficio

    # Sin plan utilizable, contesta uno solo. Quedarse callado porque el
    # director se atascó sería el peor de los resultados.
    return limpios or [{"quien": "conversación", "propio": False, "encargo": peticion}]


def _consultar(
    proveedor: Any,
    encargo: dict[str, Any],
    project: str,
    engine: Any = None,
) -> dict[str, Any]:
    quien = encargo["quien"]

    contexto = ""

    if encargo.get("propio"):
        contexto = _lo_que_ve_el_agente(quien, project)

    crudo = _hablar_con(
        proveedor,
        CONSULTA.format(
            quien=_como_se_presenta(quien, encargo.get("propio", False)),
            trato=perfil.como_llamarte(),
            encargo=encargo["encargo"] + contexto,
        ),
        engine,
        MODELO_CONSULTA,
    )

    leido = _json(crudo)

    if leido is None:
        # Sin JSON, el texto tal cual sigue siendo una respuesta.
        limpio = crudo.strip()

        return {"resumen": limpio[:300], "respuesta": limpio} if limpio else {}

    return {
        "resumen": str(leido.get("resumen") or "").strip(),
        "respuesta": str(leido.get("respuesta") or leido.get("resumen") or "").strip(),
    }


def _como_se_presenta(quien: str, propio: bool) -> str:
    if propio:
        return f"el agente de {quien} de este proyecto"

    return "el arquitecto" if es_charla(quien) else f"un experto en {quien}"


def _lo_que_ve_el_agente(quien: str, project: str) -> str:
    """Los hallazgos de verdad del agente, para que no se los invente.

    Es la diferencia entera entre este modo y responder de memoria: el de
    seguridad contesta sobre los secretos que **hay**, no sobre los que
    suele haber.
    """
    try:
        from ai_architect.commands import agents

        salida = agents.run(project)

    except Exception:  # noqa: BLE001 - sin hallazgos se contesta igual
        return ""

    hallazgos = (salida or {}).get("findings") or (salida or {}).get("results") or {}

    trozo = json.dumps(hallazgos, ensure_ascii=False, default=str)[:2500]

    return f"\n\nLo que el análisis del repositorio ha encontrado:\n{trozo}"


# --- Juntar las respuestas ---------------------------------------------------


def _ordenar(reparto: dict[str, Any], plan: list[dict[str, Any]]) -> list[tuple]:
    """En el orden en que se pidieron, no en el que contestaron.

    El reparto es paralelo y el orden de llegada es el azar de la red; el
    del plan es el que tiene sentido para quien lee.
    """
    resultados = reparto.get("results", reparto)

    return [(e["quien"], resultados.get(e["quien"])) for e in plan]


def _hablado(contestaron: list[tuple]) -> str:
    if len(contestaron) == 1:
        quien, salida = contestaron[0]

        # Se nombra siempre a quien contesta. Una respuesta anónima y una
        # respuesta del agente que ha leído tu código suenan igual, y no
        # valen lo mismo: decirlo es la mitad de la información.
        if es_charla(quien):
            return str(salida["resumen"])

        return f"Te contesta {quien}. {salida['resumen']}"

    # Con varios se dice quién dijo qué: oír dos párrafos seguidos sin saber
    # de quién son no se sigue.
    return " ".join(
        f"{quien.capitalize()}: {salida['resumen']}" for quien, salida in contestaron
    )


def _escrito(contestaron: list[tuple]) -> str:
    if len(contestaron) == 1:
        return str(contestaron[0][1]["respuesta"])

    return "\n\n".join(
        f"— {quien.upper()} —\n{salida['respuesta']}" for quien, salida in contestaron
    )


def _titulo(contestaron: list[tuple]) -> str:
    quienes = ", ".join(quien for quien, _ in contestaron)

    return quienes[:60]


# Dirigir es clasificar: de una frase, un nombre. Va en el modelo rapido.
# Contestar como experto no, pero tampoco hacen falta 37 segundos: con el
# modelo por defecto una explicacion de bachillerato tardaba mas que
# buscarla, y eso ya no es una respuesta, es una espera.
MODELO_CONSULTA = "gpt-4o"


def _hablar_con(proveedor: Any, orden: str, engine: Any, modelo: str) -> str:
    """Le pide al proveedor, en el modelo que toque, con repliegue.

    Un motor inyectado en las pruebas no tiene por que aceptar `model`, y
    una cuenta sin ese modelo tampoco: si falla, se usa el de siempre.
    """
    if engine is not None:
        return str(proveedor.generate(orden))

    try:
        return str(proveedor.generate(orden, model=modelo))

    except Exception:  # noqa: BLE001 - se cae al modelo por defecto
        return str(proveedor.generate(orden))


def _proveedor(engine: Any) -> Any:
    if engine is not None:
        return engine

    from ai_architect.providers.provider_manager import ProviderManager

    return ProviderManager()


def _json(texto: str) -> dict[str, Any] | None:
    if not texto:
        return None

    try:
        leido = json.loads(texto)

    except (ValueError, TypeError):
        hallado = re.search(r"\{.*\}", texto, re.DOTALL)

        if hallado is None:
            return None

        try:
            leido = json.loads(hallado.group(0))

        except (ValueError, TypeError):
            return None

    return dict(leido) if isinstance(leido, dict) else None
