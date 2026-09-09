"""
=========================================================
Conversar

Hablarle, en vez de escribirle.
=========================================================

Hasta aquí el arquitecto veía y hablaba, pero no oía. Y eso no se nota
hasta que alguien se pone delante, le habla, y no pasa nada — que es
exactamente lo que ocurrió.

Esto deja el servidor levantado y abre una conversación de verdad:

1. La página escucha por el micrófono y transcribe.
2. Manda lo que oyó a ``POST /orden``.
3. Aquí se interpreta con ``pide``, que elige el comando, lo ejecuta y
   redacta la respuesta.
4. Se prepara el audio, se devuelve su duración exacta, y la cara empieza
   a gesticular en el mismo instante en que empieza a sonar.
5. Vuelve a escuchar cuando termina de hablar — no antes, o se oiría a sí
   mismo por los altavoces y se contestaría solo.

**Quién transcribe.** Si hay clave de OpenAI, el audio se graba aquí y lo
transcribe Whisper, que entiende mejor el español y **acepta contexto**:
pasándole los nombres de los comandos deja de oír "revista" donde dices
"revisa". Cuesta unos seis milésimos de dólar por minuto, y solo se manda
lo que suena — el silencio lo recorta el navegador antes de enviarlo.

Sin clave se usa el reconocedor del propio Chrome: gratis, peor en español,
y manda el audio a los servidores de Google. Se dice cuál de los dos está
en uso al arrancar, porque no es un detalle.

**Se le llama por su nombre.** «Architect, revisa el proyecto». Nombrado una
vez, sigue oyendo ``SEGUIMIENTO`` segundos sin que se repita, y cada respuesta
suya reabre la ventana. Con ``--sin-nombre`` atiende todo lo que oiga, como
antes. La palabra de activación tolera recortes («arquitect») y muletillas
(«oye Architect»); ver ``ai_architect.voz.nombre``.

**Se le puede cortar.** Mientras habla, el micrófono sigue abierto. Lo que
llega en ese rato pasa por dos filtros: si es su propia voz por los altavoces
se descarta (``es_eco``); si eres tú, se corta el audio (``hablar.callar``) y
se atiende lo nuevo. «Architect, calla» lo calla sin más.

**Lo que toca archivos sigue pidiendo permiso.** Que una orden llegue por
voz no la autoriza: ``pide`` responde con lo que haría y espera. Por voz
no hay forma de teclear ``--si``, así que se arranca con ``--si`` o no se
autoriza nada. Dicho de otro modo: la decisión se toma al abrir la
conversación, no en mitad de ella.
"""

from __future__ import annotations

import json
import queue
import secrets
import threading
import time
import webbrowser
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from ai_architect.agente import progreso
from ai_architect.commands import avatar, conversar_servidor, pendientes
from ai_architect.commands.conversar_muletillas import (  # noqa: F401 - la API sigue aquí
    MERECE_RELLENO,
    RELLENOS,
    _apartar,
    _rellenos_listos,
    preparar_rellenos,
    soltar_relleno,
)
from ai_architect.core import perfil
from ai_architect.core.texto import sin_adornos
from ai_architect.voz import hablar as motor_de_voz
from ai_architect.voz import nombre as oido_nombre

# Lo que se espera del navegador en una sola orden. Una transcripción de
# más de esto no es una frase, es un micro abierto en una reunión.
LIMITE = 4000

# Lo que se oye y lo que se contesta queda también en disco. La consola se
# cierra con la ventana, y «a veces me dice que hay código mal» no se puede
# mirar sin saber qué se dijo exactamente.
REGISTRO = "conversacion.log"


def ruta_registro() -> Path:
    from ai_architect.agente.rutas_agente import get_config_dir

    return get_config_dir() / REGISTRO


def _registro(linea: str) -> None:
    """A la consola y al registro. Nunca lanza: es un extra."""
    print(linea, flush=True)

    try:
        with ruta_registro().open("a", encoding="utf-8") as archivo:
            archivo.write(time.strftime("%Y-%m-%d %H:%M:%S ") + linea.strip() + "\n")

    except OSError:
        pass


def run(
    project: str = ".",
    si: bool = False,
    servir_para_siempre: bool = True,
    nombre: bool = True,
    flotante: bool = False,
) -> dict[str, Any]:
    """Abre la cara en modo conversación y se queda escuchando.

    ``nombre``: si hay que llamarlo «Architect» para que atienda (lo normal), o
    si atiende todo lo que oiga (``--sin-nombre``). ``flotante``: en una ventana
    propia, sin marco y siempre encima (pywebview), en vez del navegador.
    """
    configurar_oido("nombre" if nombre else "libre")

    # Lo que haga se cuenta en vivo y la página lo va pidiendo (`/progreso`).
    progreso.suscribir(_bitacora.anotar)
    _bitacora.limpiar()

    if not avatar.ROSTRO.is_file():
        return {"success": False, "error": f"no encuentro el rostro en {avatar.ROSTRO}"}

    pagina = _componer(project)

    servidor, url = _levantar(pagina, project, si)

    if servidor is None:
        return {
            "success": False,
            "error": (
                f"el puerto {avatar.PUERTO} está ocupado. "
                "Cierra la otra conversación y vuelve a intentarlo."
            ),
        }

    # Antes de abrir nada: si se sintetizan al vuelo, la muletilla llega
    # tarde y entonces no tapa la espera, la alarga.
    listas = preparar_rellenos()

    # Las tareas programadas se miran mientras la conversacion este
    # abierta. Con el programa cerrado hace falta que alguien lo despierte,
    # y de eso sabe Windows: `architect tareas --correr` es lo que se
    # registra en el Programador de tareas.
    _vigilar_tareas()

    # Cada sesion empieza con un saludo, y solo uno: "Buenas tardes,
    # Efrain" delante de cada respuesta cansa a la tercera.
    from ai_architect.commands import pide

    pide.reiniciar_saludo()

    # La ventana flotante bloquea hasta que se cierra, así que el servidor va
    # en un hilo. Si pywebview no está, se avisa y se abre el navegador.
    en_ventana = flotante and avatar.hay_ventana_flotante()

    if flotante and not en_ventana:
        print(avatar.SIN_VENTANA, flush=True)

    if not en_ventana:
        webbrowser.open(url)

    aviso = (
        f"{perfil.encabezar()} Te escucho.\n\n"
        f"  Habla en voz alta. Lo que entienda te lo escribo en la pantalla,\n"
        f"  para que si me equivoco lo veas al momento.\n\n"
        f"  Órdenes que tocan archivos: {'autorizadas' if si else 'NO autorizadas'}"
        f"{'' if si else ' (arranca con --si para permitirlas)'}.\n"
        f"  Te oye: {_quien_oye()}\n"
        f"  Muletillas listas: {listas} (dice algo mientras trabaja)\n\n"
        f"{_como_llamarlo()}\n\n"
        f"  Ctrl+C para terminar.\n"
    )

    print(aviso, flush=True)

    if servir_para_siempre and en_ventana:
        threading.Thread(target=servidor.serve_forever, daemon=True).start()

        try:
            avatar.ventana_flotante(url)

        except KeyboardInterrupt:
            pass

        finally:
            print(f"\n{perfil.despedir()}")
            _apagar(servidor)

    elif servir_para_siempre:
        try:
            servidor.serve_forever()

        except KeyboardInterrupt:
            print(f"\n{perfil.despedir()}")

        finally:
            _apagar(servidor)

    return {
        "success": True,
        "url": url,
        "authorised": si,
        "wake_word": nombre,
        "floating": en_ventana,
    }


# --- Lo que va haciendo, y el permiso ---------------------------------------
#
# `hacer` cuenta cada herramienta y cada escritura que se le negó; la página lo
# pide por `/progreso` y lo enseña en tarjetas. Cuando termina con cambios en
# cola, la cara se pone en ámbar y pregunta; se contesta con la voz («sí», «no»)
# o con los botones (`/permiso`), y los cambios se aplican o se descartan desde
# la cola de aprobaciones de la fase 2.

_bitacora = progreso.Bitacora()

# Los cambios que están esperando un «sí»: id y descripción.
_permiso_pendiente: list[dict[str, str]] = []

AFIRMA = frozenset(
    {
        "si",
        "si claro",
        "claro",
        "dale",
        "hazlo",
        "adelante",
        "aprobado",
        "aprueba",
        "apruebalo",
        "de acuerdo",
        "ok",
        "okey",
        "vale",
        "confirmo",
        "procede",
        "aplica",
        "aplicalo",
        "aplicalos",
        "que si",
        "si hazlo",
        "si aplicalo",
        "si adelante",
        "si dale",
    }
)

NIEGA = frozenset(
    {
        "no",
        "que no",
        "no lo hagas",
        "no lo apliques",
        "rechaza",
        "rechazalo",
        "rechazalos",
        "cancela",
        "cancelalo",
        "dejalo",
        "dejalo asi",
        "nada",
        "no gracias",
        "mejor no",
        "descarta",
        "descartalo",
        "descartalos",
        "todavia no",
        "aun no",
    }
)


def progreso_desde(n: int) -> dict[str, Any]:
    return _bitacora.desde(n)


def hay_permiso_pendiente() -> bool:
    return bool(_permiso_pendiente)


def decidir_permiso(texto: str) -> str:
    """``"si"``, ``"no"`` o ``""`` si eso no era una respuesta al permiso."""
    plano = sin_adornos(texto)

    if not plano:
        return ""

    if plano in AFIRMA:
        return "si"

    if plano in NIEGA:
        return "no"

    palabras = plano.split()

    if len(palabras) <= 3 and palabras[0] == "si":
        return "si"

    if len(palabras) <= 3 and palabras[0] == "no":
        return "no"

    return ""


def _anotar_permiso(resultado: dict[str, Any]) -> list[str]:
    """Si el comando dejó cambios en cola, se recuerdan para el próximo «sí»."""
    global _permiso_pendiente

    fuente = (
        resultado.get("result")
        if isinstance(resultado.get("result"), dict)
        else resultado
    )
    ids = list((fuente or {}).get("pending_ids") or [])
    textos = list((fuente or {}).get("pending") or [])

    if not ids:
        return []

    _permiso_pendiente = [
        {"id": i, "descripcion": (textos[k] if k < len(textos) else i)}
        for k, i in enumerate(ids)
    ]

    return [p["descripcion"] for p in _permiso_pendiente]


def resolver_permiso(decision: str) -> dict[str, Any]:
    """Aplica o descarta lo que esperaba permiso, y lo dice."""
    global _permiso_pendiente

    esperando = list(_permiso_pendiente)
    _permiso_pendiente = []
    trato = perfil.como_llamarte()

    if not esperando:
        respuesta = f"No tenía nada pendiente de tu permiso, {trato}."

    elif decision == "si":
        hechos = 0

        for accion in esperando:
            salida = pendientes.aprobar(accion["id"])

            if salida.get("success") and all(
                h.startswith("✓") for h in salida.get("done", [])
            ):
                hechos += 1

        progreso.avisar("fase", fase="listo" if hechos == len(esperando) else "error")

        if hechos == len(esperando):
            respuesta = f"Listo, {trato}: apliqué {hechos} cambio(s)."
        else:
            respuesta = (
                f"Apliqué {hechos} de {len(esperando)} cambio(s), {trato}; "
                "el resto falló. Míralo con architect pendientes."
            )

    else:
        for accion in esperando:
            pendientes.rechazar(accion["id"])

        progreso.avisar("fase", fase="descartado")

        respuesta = f"Descartado, {trato}: no toqué nada."

    _registro(f"  > (permiso: {decision})")

    preparado = motor_de_voz.preparar(respuesta)

    _recordar_dicho(preparado, respuesta)

    return {
        "respuesta": respuesta,
        "dicho": preparado.get("texto", respuesta),
        "ms": int(float(preparado.get("segundos", 0) or 0) * 1000),
        "instantanea": True,
        "permiso_resuelto": decision,
        "_audio": preparado,
    }


def _como_llamarlo() -> str:
    if _modo_oido == "nombre":
        return (
            "  Llámalo por su nombre: «Architect, revisa el proyecto». Después de\n"
            f"  nombrarlo te sigue oyendo {int(SEGUIMIENTO)} s sin que lo repitas.\n"
            "  Si está hablando y quieres cortarlo, háblale encima: «Architect, calla».\n"
            "  (--sin-nombre para que atienda todo lo que oiga)"
        )

    return (
        "  Háblale sin más: no hace falta llamarlo por su nombre.\n"
        "  Si está hablando y quieres cortarlo, háblale encima."
    )


# Cada cuanto se mira si toca alguna. Un minuto: mas seguido es gastar
# lecturas de disco para nada, y menos se nota en una tarea "a las diez".
LATIDO = 60.0


def _vigilar_tareas() -> None:
    """Un hilo que ejecuta lo programado y lo cuenta en voz alta."""
    from ai_architect.commands import tareas

    def vigilar() -> None:
        while True:
            time.sleep(LATIDO)

            try:
                hechas = tareas.correr()

            except Exception:  # noqa: BLE001 - una tarea rota no calla la voz
                continue

            for hecha in hechas:
                dicho = str(hecha.get("explanation") or hecha.get("error") or "")

                print(f"  ~ tarea: {hecha['name']} -> {_resumen(dicho)}", flush=True)

                # Se dice en voz alta: una tarea que se ejecuta en silencio
                # es indistinguible de una que no se ejecuto.
                motor_de_voz.emitir(motor_de_voz.preparar(dicho))

    threading.Thread(target=vigilar, daemon=True).start()


def _quien_oye() -> str:
    from ai_architect.voz import escuchar

    if escuchar.disponible():
        return "Whisper (OpenAI), con vocabulario del proyecto. ~$0.006/minuto"

    return "el reconocedor de Chrome — gratis, peor en español, pasa por Google"


# Quien tiene ahora mismo el microfono. Cada carga de la pagina se lleva
# uno nuevo, y solo el ultimo vale.
_turno = ""


def _componer(project: str) -> str:
    from ai_architect.voz import escuchar

    global _turno

    _turno = secrets.token_hex(8)

    datos = {
        "turno": _turno,
        "ms": 0,
        "texto": "",
        "modo": "conversacion",
        "proyecto": project,
        # Sin clave no hay Whisper, y callarlo sería peor: se notaría que
        # entiende peor y no habría forma de saber por qué.
        "oido": "whisper" if escuchar.disponible() else "navegador",
        "modo_oido": _modo_oido,
        "nombre": "Architect",
    }

    return avatar.ROSTRO.read_text(encoding="utf-8").replace(
        avatar.MARCA,
        "window.DATOS_ARQUITECTO = " + json.dumps(datos, ensure_ascii=False) + ";",
        1,
    )


# Lo ultimo que dijo el arquitecto en voz alta, para reconocerlo si le vuelve
# por el microfono.
_ultimo_dicho = ""


def es_eco(oido: str, dicho: str) -> bool:
    """Si lo que se acaba de oir es la propia voz saliendo por los altavoces.

    El navegador ya se tapa los oidos mientras habla, pero eso depende de
    que su reloj y el del audio vayan a la par —y no van—, y de que no haya
    dos pestanas abiertas escuchando a la vez. Aqui se comprueba lo unico
    que no enga:na: si lo oido es lo que se acaba de decir. Aunque llegue
    tarde, aunque llegue por otra pestana.
    """
    a = sin_adornos(oido)
    b = sin_adornos(dicho)

    if not a or not b:
        return False

    # Con menos de tres palabras no se puede juzgar: "si", "ya" o "para"
    # son ordenes legitimas y aparecen en cualquier respuesta.
    if len(a.split()) < 3:
        return False

    if a in b:
        return True

    return SequenceMatcher(None, a, b).ratio() > 0.62


# Cómo se le llama. La lógica vive en ``ai_architect.voz.nombre``; aquí queda
# el estado de la sesión: el modo y cuándo se le habló por última vez.
NOMBRES = oido_nombre.NOMBRES

# Cuánto dura la ventana tras nombrarlo o tras contestar.
SEGUIMIENTO = oido_nombre.SEGUIMIENTO

# "nombre": hay que llamarlo (salvo dentro de la ventana). "libre": todo va para él.
_modo_oido = "libre"

_ultima_vez = 0.0


def configurar_oido(modo: str) -> None:
    """Cómo decide a quién atiende. ``"nombre"`` o ``"libre"``."""
    global _modo_oido

    if modo not in oido_nombre.MODOS:
        raise ValueError(f"modo de oído desconocido: {modo}")

    _modo_oido = modo


def dirigido_a_mi(texto: str, ahora: float | None = None) -> tuple[bool, str]:
    """Si eso iba para él, y qué queda al quitarle el nombre.

    En modo ``libre`` se acepta lo que llegue (la primera versión con palabra
    clave falló porque el micrófono recortaba «arquitecto» a «arquitect»; de
    la propia voz por los altavoces se encarga ``es_eco``). En modo ``nombre``
    hay que llamarlo, con tolerancia al recorte y con ventana de seguimiento.
    Si viene el nombre delante, se quita: «arquitecto, revisa» es «revisa».
    """
    global _ultima_vez

    decision = oido_nombre.decidir(
        texto,
        modo=_modo_oido,
        ultima_vez=_ultima_vez,
        ahora=ahora,
        seguimiento=SEGUIMIENTO,
    )

    if decision.nombrado:
        # Nombrarlo abre la ventana: lo que venga después ya no necesita el nombre.
        _ultima_vez = time.monotonic() if ahora is None else ahora

    return (decision.para_mi, decision.orden)


# --- Cortarlo a media frase ---------------------------------------------------

# Lo que se dice para que se calle. Solo cuenta mientras está hablando: un
# «para» a secas en silencio sigue siendo una orden normal.
PARAR = frozenset(
    {
        "calla",
        "callate",
        "calla ya",
        "callate ya",
        "para",
        "para ya",
        "para de hablar",
        "deja de hablar",
        "basta",
        "basta ya",
        "silencio",
        "espera",
        "espera un momento",
        "un momento",
        "stop",
        "alto",
        "chito",
        "shh",
        "ya",
        "no sigas",
        "cierra el pico",
    }
)


def es_orden_de_parar(texto: str) -> bool:
    plano = sin_adornos(texto)

    if not plano:
        return False

    if plano in PARAR:
        return True

    palabras = plano.split()

    return (
        palabras[0] in ("calla", "callate", "basta", "silencio") and len(palabras) <= 4
    )


def _olvidar_lo_dicho() -> None:
    """Lo cortaron: lo que iba a decir ya no puede volver como eco."""
    global _ultimo_dicho

    _ultimo_dicho = ""


def _recordar_dicho(preparado: dict[str, Any], respuesta: str) -> None:
    """Deja apuntado lo que va a decir (para el eco) y cuándo termina (ventana)."""
    global _ultimo_dicho, _ultima_vez

    _ultimo_dicho = str(preparado.get("texto", "") or respuesta)

    # La cuenta empieza cuando **acaba de hablar**, no cuando prepara la
    # respuesta. Sumarle la duración del audio es exactamente eso: si va a
    # hablar treinta segundos, la ventana no se abre hasta el final.
    #
    # Sin esto, una respuesta larga se comía la ventana entera y la
    # siguiente frase —la de verdad, la del usuario— se descartaba con un
    # "no era para mí". Que es justo lo contrario de lo que hace falta.
    _ultima_vez = time.monotonic() + float(preparado.get("segundos", 0) or 0)


def responder_al_nombre() -> dict[str, Any]:
    """«Architect» a secas: es llamarlo. Se contesta corto y se abre la ventana."""
    dicho = f"Dime, {perfil.como_llamarte()}."

    preparado = motor_de_voz.preparar(dicho)

    _recordar_dicho(preparado, dicho)

    return {
        "respuesta": dicho,
        "dicho": preparado.get("texto", dicho),
        "ms": int(float(preparado.get("segundos", 0) or 0) * 1000),
        "instantanea": True,
        "_audio": preparado,
    }


def atender_lo_dicho(
    texto: str, project: str, si: bool, *, interrumpe: bool = False
) -> dict[str, Any]:
    """La vía del reconocedor del navegador: texto ya transcrito, respuesta en la
    misma petición. ``interrumpe`` es que llegó mientras él hablaba."""
    limpio = (texto or "").strip()

    if interrumpe and (
        es_eco(limpio, _ultimo_dicho) or len(sin_adornos(limpio).split()) < 2
    ):
        return {"respuesta": "", "dicho": "", "ms": 0, "error": "eco"}

    para_mi, orden = dirigido_a_mi(limpio)

    if limpio and not para_mi:
        _registro(f"  · (no era para mí) {limpio}")

        return {"respuesta": "", "dicho": "", "ms": 0, "ajeno": True, "oido": limpio}

    cortado = motor_de_voz.callar() if interrumpe else False

    if cortado:
        _registro("  ! (interrumpido)")

    if interrumpe and es_orden_de_parar(orden):
        _olvidar_lo_dicho()

        return {"respuesta": "", "dicho": "", "ms": 0, "callado": True, "oido": limpio}

    nombrado, resto = oido_nombre.separar(limpio)

    if nombrado and not resto:
        return {**responder_al_nombre(), "oido": limpio, "interrumpido": cortado}

    _registro(f"  > {orden}")

    return {**atender(orden, project, si), "interrumpido": cortado}


def atender_lo_oido(
    dicho: str,
    project: str,
    si: bool,
    *,
    interrumpe: bool = False,
    error: str = "",
) -> dict[str, Any]:
    """La vía de Whisper: decide qué hacer con una frase oída y, si es una
    orden, la lanza aparte y devuelve un resguardo."""
    if not dicho:
        # Ni se ejecuta ni se contesta. Lo que no se entendió no se
        # adivina, y soltar "no te entendí" a cada ruido de la
        # habitación acabaría siendo insoportable.
        return {"oido": "", "respuesta": "", "ms": 0, "error": error or "nada"}

    nombrado, resto = oido_nombre.separar(dicho)

    # Mientras habla, un trozo corto sin su nombre es casi seguro su propia
    # voz llegando a cachos: con menos de tres palabras `es_eco` no puede
    # juzgar, así que aquí se descarta directamente.
    if interrumpe and not nombrado and len(sin_adornos(dicho).split()) < 3:
        _registro(f"  ~ (eco descartado) {dicho}")

        return {"oido": "", "respuesta": "", "ms": 0, "error": "eco"}

    if es_eco(dicho, _ultimo_dicho):
        # Se oyó a sí mismo por los altavoces. Ni se ejecuta ni se
        # contesta: contestar sería empezar una conversación consigo
        # mismo que no para hasta que alguien cierre la pestaña.
        _registro(f"  ~ (eco descartado) {dicho}")

        return {"oido": "", "respuesta": "", "ms": 0, "error": "eco"}

    # Solo lo que va dirigido a él. Un micrófono abierto oye la tele, a
    # quien pasa por detrás y a quien habla por teléfono al lado.
    para_mi, orden = dirigido_a_mi(dicho)

    if not para_mi:
        _registro(f"  · (no era para mí) {dicho}")

        return {"oido": dicho, "ajeno": True, "respuesta": "", "ms": 0}

    cortado = motor_de_voz.callar() if interrumpe else False

    if cortado:
        _registro("  ! (interrumpido)")

    if interrumpe and es_orden_de_parar(orden):
        _olvidar_lo_dicho()

        _registro("  > (calla)")

        return {"oido": dicho, "callado": True, "respuesta": "", "ms": 0}

    if nombrado and not resto:
        _registro("  > (me llamó)")

        return {**responder_al_nombre(), "oido": dicho, "interrumpido": cortado}

    _registro(f"  > {orden}")

    # Se contesta ya, con un resguardo, y el trabajo se hace aparte.
    # Antes esta respuesta tardaba lo que tardara el comando entero
    # —hasta medio minuto con los agentes— y en todo ese rato la
    # cara no decía ni hacía nada. Ahora la página sabe al instante
    # que se le oyó, y va a buscar la respuesta cuando esté.
    resguardo = secrets.token_hex(6)

    buzon: queue.Queue = queue.Queue(maxsize=1)

    _pendientes[resguardo] = buzon

    threading.Thread(
        target=_trabajar,
        args=(buzon, orden, project, si),
        daemon=True,
    ).start()

    return {"oido": orden, "resguardo": resguardo, "interrumpido": cortado}


def atender(texto: str, project: str, si: bool) -> dict[str, Any]:
    """Interpreta una orden dicha en voz alta y prepara la respuesta.

    Separado del servidor a propósito: así se puede probar la conversación
    entera sin abrir un puerto ni un navegador.
    """
    from ai_architect.commands import pide

    orden = (texto or "").strip()[:LIMITE]

    if not orden:
        return {"respuesta": "No te entendí.", "dicho": "No te entendí.", "ms": 0}

    # Si acaba de pedir permiso, un «sí» o un «no» es la respuesta a eso, no
    # una orden nueva.
    if _permiso_pendiente:
        decision = decidir_permiso(orden)

        if decision:
            return resolver_permiso(decision)

    resultado = pide.run(project, frase=orden, si=si)

    respuesta = str(resultado.get("explanation") or resultado.get("error") or "")

    permiso = _anotar_permiso(resultado)

    if permiso:
        respuesta = (
            respuesta.rstrip()
            + f"\n\nTengo {len(permiso)} cambio(s) esperando tu permiso. ¿Los aplico?"
        )

    preparado = motor_de_voz.preparar(respuesta)

    _recordar_dicho(preparado, respuesta)

    return {
        "respuesta": respuesta,
        "dicho": preparado.get("texto", respuesta),
        "ms": int(preparado.get("segundos", 0) * 1000),
        "panel": resultado.get("panel"),
        "ventana": resultado.get("window", ""),
        "instantanea": bool(resultado.get("instant")),
        "permiso": permiso,
        "_audio": preparado,
    }


# Trabajos en marcha, por resguardo. La página deja el suyo y vuelve a
# recogerlo; entretanto el arquitecto dice algo en vez de callarse.
_pendientes: dict[str, queue.Queue] = {}

# Tope de paciencia. `agents --ai` con cinco llamadas puede irse lejos, pero
# no infinito: un buzón que nunca se vacía deja la página colgada.
ESPERA_TRABAJO = 180.0


def _trabajar(buzon: queue.Queue, dicho: str, project: str, si: bool) -> None:
    """Hace la tarea, y si tarda dice algo mientras.

    El relleno no se elige por adivinanza: se lanza el trabajo, se le dan
    ``MERECE_RELLENO`` segundos, y solo si sigue vivo se habla. Así una
    pregunta instantánea no lleva un "dame un segundo" pegado delante.
    """
    caja: dict[str, Any] = {}

    faena = threading.Thread(
        target=lambda: caja.update(atender(dicho, project, si)),
        daemon=True,
    )

    faena.start()
    faena.join(MERECE_RELLENO)

    if faena.is_alive():
        muletilla = soltar_relleno()

        if muletilla:
            _registro(f"  · {muletilla.get('texto', '')}")

    faena.join(ESPERA_TRABAJO)

    # El buzón llega por parámetro, no se busca por su nombre. Buscarlo era
    # un fallo de los que no se ven leyendo: la página pide la respuesta en
    # cuanto le dan el resguardo —o sea, casi siempre antes de que la tarea
    # termine—, y al pedirla se sacaba el buzón del diccionario. Cuando la
    # tarea acababa ya no encontraba dónde dejar el resultado, lo tiraba, y
    # la página se quedaba esperando algo que nunca iba a llegar.
    try:
        buzon.put_nowait(
            caja
            or {
                "respuesta": "Algo se me atragantó y no pude terminar.",
                "dicho": "Algo se me atragantó y no pude terminar.",
                "ms": 0,
            }
        )

    except queue.Full:
        pass


def _resumen(respuesta: str) -> str:
    """El meollo de la respuesta, sin el saludo ni la despedida.

    Se imprimia la primera linea y la primera linea siempre es "Buenas
    tardes, Efrain": el registro de una conversacion entera decia lo mismo
    en todas las lineas y no servia para nada.
    """
    partes = [t.strip() for t in respuesta.split(chr(10) * 2) if t.strip()]

    return partes[1] if len(partes) > 2 else (partes[0] if partes else "")


UnSoloDuenio = conversar_servidor.UnSoloDuenio


def _levantar(pagina: str, project: str, si: bool) -> tuple[Any, str]:
    """El servidor vive en ``conversar_servidor``; esto queda para quien lo
    llamaba (y para las pruebas, que lo doblan aquí)."""
    return conversar_servidor.levantar(pagina, project, si)


def _apagar(servidor: Any) -> None:
    conversar_servidor.apagar(servidor)


def rostro() -> Path:
    return avatar.ROSTRO
