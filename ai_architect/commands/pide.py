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

from pathlib import Path
from typing import Any, cast

from ai_architect.commands.pide_guion import (  # noqa: F401 - la API del módulo sigue aquí
    CORTESIA,
    DIAS,
    INSTRUCCIONES,
    MESES,
    _merece_experto,
    _momento,
)
from ai_architect.commands.pide_modelo import (  # noqa: F401 - la API del módulo sigue aquí
    MODELOS_RAPIDOS,
    _catalogo,
    _preguntar,
)
from ai_architect.commands.pide_orden import (  # noqa: F401 - la API del módulo sigue aquí
    BANDERAS_QUE_ESCRIBEN,
    MODIFICAN,
    _argumentos,
    _como_se_escribe,
    _error,
    _leer_json,
)
from ai_architect.commands.pide_respuesta import (  # noqa: F401 - la API del módulo sigue aquí
    _explicar_mejora,
    explicar,
    panel,
)
from ai_architect.core import gasto, perfil


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
                    # El ejemplo llevaba un nombre real escrito a mano, y en
                    # un equipo compartido eso es proponerle a alguien que
                    # se llame como su compañero.
                    "¿Cómo quieres que te llame? Dímelo así:\n"
                    '    architect pide --soy "tu nombre"',
                    f"Me hizo {perfil.quien_te_hizo()}.",
                ]
            ),
        }

    # Si acaba de preguntar donde guardar algo, la frase siguiente es la
    # respuesta a eso y no una orden nueva. Mandarla al modelo seria pedirle
    # que adivine el contexto que ya tenemos aqui.
    # Si preguntó dónde está el repositorio, la frase siguiente es la
    # respuesta a eso. Mandarla al modelo sería pedirle que adivine un
    # contexto que está aquí al lado.
    from ai_architect.commands import crear, encargo

    if encargo.hay_encargo():
        vuelta = encargo.con_el_sitio(frase, repositorio)

        if vuelta is not None and not vuelta.get("listo"):
            return _decir_si_toca(
                {
                    "success": True,
                    "executed": False,
                    "command": "",
                    "instant": True,
                    "explanation": _con_trato(vuelta["explanation"]),
                },
                decir,
                cara,
            )

        if vuelta is not None:
            return _ejecutar(
                vuelta["comando"],
                vuelta["intencion"],
                vuelta["sitio"],
                vuelta["frase"],
                si,
                decir,
                cara,
            )

    # Programar, pausar o listar tareas son cuatro verbos y una hora.
    # Mandarlo al modelo son dos segundos para entender algo ya dicho.
    from ai_architect.commands import tareas

    de_tareas = tareas.por_voz(frase, str(repositorio))

    if de_tareas is not None:
        return _decir_si_toca(
            {
                "success": de_tareas.get("success", True),
                "executed": bool(de_tareas.get("task")),
                "command": "tareas",
                "instant": True,
                "explanation": _con_trato(de_tareas["explanation"]),
            },
            decir,
            cara,
        )

    # "Pasalo a Word" va antes que nada: se refiere a lo que se acaba de
    # decir, y mandarlo al modelo era pedirle que adivinara un contexto que
    # esta aqui al lado.
    aword = crear.pedir_word(frase)

    if aword is not None:
        return _decir_si_toca(
            {
                "success": True,
                "executed": False,
                "command": "crear",
                "instant": True,
                "panel": aword.get("panel"),
                "explanation": _con_trato(aword["explanation"]),
            },
            decir,
            cara,
        )

    if crear.hay_pendiente():
        destino = crear.donde_guardarlo(frase)

        if destino is not None:
            return _decir_si_toca(
                {
                    "success": destino.get("success", True),
                    "executed": bool(destino.get("path")),
                    "command": "crear",
                    "instant": True,
                    "path": destino.get("path", ""),
                    "panel": destino.get("panel"),
                    "explanation": _con_trato(
                        destino.get("explanation") or destino.get("error", "")
                    ),
                },
                decir,
                cara,
            )

    # Antes que nada, lo que no necesita a nadie. "Que hora es" tardaba tres
    # segundos y costaba dinero para leer un reloj que esta en la maquina.
    from ai_architect.commands import respuestas

    rapida = respuestas.responder(frase)

    if rapida is not None:
        return _decir_si_toca(
            {
                "success": True,
                "executed": False,
                "command": "",
                "conversation": True,
                "instant": True,
                "panel": rapida.get("panel"),
                "window": rapida.get("ventana", ""),
                "explanation": _con_trato(rapida["respuesta"]),
            },
            decir,
            cara,
        )

    catalogo, tabla = _catalogo()

    try:
        cruda = _preguntar(engine, catalogo, frase, str(repositorio))

    except gasto.TopeAlcanzado as tope:
        # No es una avería: es lo que se le pidió que hiciera.
        return _error(str(tope))

    except Exception as e:  # noqa: BLE001 - un proveedor caído no revienta
        from ai_architect.commands import configurar

        # "OPENAI_API_KEY is not configured" es correcto y no ayuda a nadie:
        # es lo primero que ve quien acaba de instalarlo, en inglés y con el
        # nombre de una variable de entorno que no tiene por qué conocer.
        if not configurar.esta_configurado():
            return _error(configurar.falta_la_clave())

        return _error(f"el proveedor falló: {e}")

    intencion = _leer_json(cruda)

    if intencion is None:
        return _error(
            "no entendí la respuesta del modelo",
            crudo=cruda[:400],
        )

    nombre = str(intencion.get("comando", "")).strip()

    if not nombre:
        # No toda frase es una orden. Un saludo, una pregunta sobre él o un
        # encargo que no va del repositorio también merecen respuesta:
        # contestar "no supe qué comando usar" a un "buenas tardes" es lo
        # que hace que una herramienta no se sienta tuya.
        charla = str(intencion.get("respuesta") or "").strip()

        # Una pregunta de verdad no la contesta el despachador: la dirige a
        # quien sepa del tema. El despachador usa el modelo rapido y su
        # trabajo es elegir, no saber; contestar con el es contestar con
        # quien menos sabe de la casa.
        if _merece_experto(frase, charla):
            from ai_architect.commands import experto

            dicho = experto.responder(frase, str(repositorio), engine=engine)

            if dicho.get("success"):
                _aprender(frase, str(dicho.get("explanation", "")), engine)
                return _decir_si_toca(
                    {
                        "success": True,
                        "executed": False,
                        "command": "",
                        "conversation": True,
                        "specialists": dicho.get("specialists", []),
                        "panel": dicho.get("panel"),
                        "written": dicho.get("written", ""),
                        "explanation": _con_trato(
                            _recordado(frase, dicho["explanation"], dicho)
                        ),
                    },
                    decir,
                    cara,
                )

        if charla:
            _aprender(frase, charla, engine)
            return _decir_si_toca(
                {
                    "success": True,
                    "executed": False,
                    "command": "",
                    "conversation": True,
                    "explanation": _con_trato(charla),
                },
                decir,
                cara,
            )

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

    dicha = str(intencion.get("carpeta") or "").strip()

    # Sin saber sobre qué repositorio, lo que haga no vale nada: `project`
    # vale "." por defecto, así que analizaba el que tuviera delante y no
    # decía nada. Cuando acierta parece listo; cuando falla, ha trabajado
    # media hora sobre el proyecto equivocado.
    if encargo.falta_el_sitio(frase, nombre, dicha):
        return _decir_si_toca(
            {**encargo.anotar(nombre, frase, intencion), "instant": True},
            decir,
            cara,
        )

    if dicha:
        from ai_architect.core import rutas

        elegida, parecidas = rutas.resolver(dicha, repositorio)

        if elegida is None:
            # Ante la duda se pregunta. Ejecutar algo sobre la carpeta
            # equivocada es peor que perder un segundo confirmando.
            sugerencia = (
                f" Tengo estas cerca: {rutas.nombrar(parecidas)}." if parecidas else ""
            )

            return _decir_si_toca(
                {
                    "success": True,
                    "executed": False,
                    "command": "",
                    "conversation": True,
                    "explanation": _con_trato(
                        f"No encuentro ninguna carpeta que se llame {dicha}."
                        + sugerencia
                    ),
                },
                decir,
                cara,
            )

        repositorio = elegida

        # La carpeta dicha manda sobre el `project` del modelo, que suele
        # ser "." y ganaría por ser lo primero que mira `_argumentos`.
        intencion = {**intencion, "project": str(elegida)}

    return _ejecutar(nombre, intencion, repositorio, frase, si, decir, cara)


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


# Si ya saludó en esta sesión. "Buenas tardes, Efraín" delante de cada
# respuesta cansa a la tercera: se saluda al empezar, como haría cualquiera,
# y a partir de ahí se contesta y ya.
_ya_saludo = False


def reiniciar_saludo() -> None:
    """Vuelve a saludar la próxima vez. Se llama al abrir una sesión."""
    global _ya_saludo

    _ya_saludo = False


def _aprender(frase: str, respuesta: str, engine: Any) -> None:
    """Saca los hechos durables de la charla y los guarda, en segundo plano.

    Solo cuando hay proveedor real (con un motor inyectado, en pruebas, no se aprende)
    y salvo que ``ARCHITECT_MEMORIA_AUTO=0``. Nunca puede romper la respuesta.
    """
    try:
        from ai_architect.agente import memoria

        if memoria.auto_activa(engine):
            memoria.aprender_de(frase, respuesta)
    except Exception:  # noqa: BLE001 - la memoria es un extra
        return


def _recordado(frase: str, cuerpo: str, fuente: Any) -> str:
    """Deja apuntada la respuesta y la devuelve tal cual.

    Sin esto, "pasalo a Word" no tiene a que referirse: lo que salio en la
    ventana flotante se quedaba ahi y no habia forma de convertirlo.
    """
    from ai_architect.commands import crear

    largo = ""

    if isinstance(fuente, dict):
        largo = str(fuente.get("written") or "")

    crear.recordar(frase.strip()[:60] or "Respuesta", largo or cuerpo)

    return cuerpo


def _con_trato(cuerpo: str) -> str:
    """La respuesta, entre el saludo y la despedida del momento del día.

    Es lo que separa una herramienta de algo que se siente tuyo: que sepa a
    quién le habla y qué hora es.
    """
    global _ya_saludo

    partes = [] if _ya_saludo else [perfil.encabezar()]

    _ya_saludo = True

    partes.append(cuerpo)
    partes.append(perfil.cerrar())

    return "\n\n".join(partes)


def _ejecutar(
    nombre: str,
    intencion: dict[str, Any],
    repositorio: Any,
    frase: str,
    si: bool,
    decir: bool,
    cara: bool,
) -> dict:
    """Corre el comando elegido y redacta la respuesta.

    Separado de `run` porque hay dos caminos que llegan aqui: la frase que
    lo dice todo de una vez, y la que se resolvio a medias —"analicemos un
    repositorio", "autosgsst"— y llega con el sitio ya sabido.
    """
    from ai_architect.cli import POR_NOMBRE

    comando = POR_NOMBRE[nombre]

    args = _argumentos(intencion, str(repositorio), si=si)

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
        # `Comando.ejecutar` está tipado para el `Namespace` de argparse, y
        # aquí se le pasa uno construido a mano con los mismos campos. Es
        # deliberado: `pide` no viene de la línea de órdenes, pero ejecuta
        # exactamente los mismos comandos y no va a haber dos tablas.
        resultado = comando.ejecutar(cast(Any, args))

    except Exception as e:  # noqa: BLE001 - el comando falla, `pide` informa
        return _error(f"{nombre} falló: {e}", command=nombre)

    respuesta = {
        "success": True,
        "executed": True,
        "command": nombre,
        "ran": orden,
        "explanation": _con_trato(
            _recordado(frase, explicar(nombre, resultado), resultado)
        ),
        "panel": panel(nombre, resultado),
        "result": resultado,
    }

    return _decir_si_toca(respuesta, decir, cara)
