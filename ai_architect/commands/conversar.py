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

**Lo que toca archivos sigue pidiendo permiso.** Que una orden llegue por
voz no la autoriza: ``pide`` responde con lo que haría y espera. Por voz
no hay forma de teclear ``--si``, así que se arranca con ``--si`` o no se
autoriza nada. Dicho de otro modo: la decisión se toma al abrir la
conversación, no en mitad de ella.
"""

from __future__ import annotations

import http.server
import json
import queue
import random
import secrets
import threading
import time
import webbrowser
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from ai_architect.commands import avatar
from ai_architect.core import perfil
from ai_architect.core.texto import sin_adornos
from ai_architect.voz import hablar as motor_de_voz

# Lo que se espera del navegador en una sola orden. Una transcripción de
# más de esto no es una frase, es un micro abierto en una reunión.
LIMITE = 4000


def run(
    project: str = ".",
    si: bool = False,
    servir_para_siempre: bool = True,
) -> dict[str, Any]:
    """Abre la cara en modo conversación y se queda escuchando."""
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

    # Cada sesion empieza con un saludo, y solo uno: "Buenas tardes,
    # Efrain" delante de cada respuesta cansa a la tercera.
    from ai_architect.commands import pide

    pide.reiniciar_saludo()

    webbrowser.open(url)

    aviso = (
        f"{perfil.encabezar()} Te escucho.\n\n"
        f"  Habla en voz alta. Lo que entienda te lo escribo en la pantalla,\n"
        f"  para que si me equivoco lo veas al momento.\n\n"
        f"  Órdenes que tocan archivos: {'autorizadas' if si else 'NO autorizadas'}"
        f"{'' if si else ' (arranca con --si para permitirlas)'}.\n"
        f"  Te oye: {_quien_oye()}\n"
        f"  Muletillas listas: {listas} (dice algo mientras trabaja)\n\n"
        f"  LLÁMALO POR SU NOMBRE para empezar:\n"
        f'      "Arquitecto, revisa el proyecto"\n'
        f"  Después sigue la conversación {int(SEGUIMIENTO)} s sin repetirlo.\n\n"
        f"  Ctrl+C para terminar.\n"
    )

    print(aviso, flush=True)

    if servir_para_siempre:
        try:
            servidor.serve_forever()

        except KeyboardInterrupt:
            print(f"\n{perfil.despedir()}")

        finally:
            _apagar(servidor)

    return {"success": True, "url": url, "authorised": si}


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


# Lo que dice mientras trabaja. Una cara callada durante tres segundos
# parece colgada; con esto se sabe que te oyó y está en ello.
#
# Varias y al azar para que no suene a grabación. Se sintetizan una sola vez
# al arrancar —con Piper son milisegundos— porque generarlas en el momento
# añadiría justo la espera que vienen a tapar.
RELLENOS = (
    "Dame un segundo.",
    "Voy con eso.",
    "Un momento, lo miro.",
    "Enseguida te digo.",
    "Déjame ver.",
)

# Por debajo de esto no da tiempo ni a abrir la boca: decir "dame un
# segundo" y contestar en el mismo aliento queda peor que no decir nada.
MERECE_RELLENO = 0.9

_rellenos_listos: list[dict[str, Any]] = []


def preparar_rellenos() -> int:
    """Deja las muletillas sintetizadas antes de que hagan falta."""
    _rellenos_listos.clear()

    for frase in RELLENOS:
        listo = motor_de_voz.preparar(frase)

        if listo.get("archivo") or listo.get("motor") == "windows":
            # Cada una en su archivo: comparten el temporal de `hablar` y
            # la última pisaría a todas las anteriores.
            copia = _apartar(listo, len(_rellenos_listos))

            if copia:
                _rellenos_listos.append(copia)

    return len(_rellenos_listos)


def _apartar(listo: dict[str, Any], indice: int) -> dict[str, Any] | None:
    origen = listo.get("archivo")

    if origen is None:
        return dict(listo)

    destino = Path(origen).with_name(f"arquitecto-relleno-{indice}.wav")

    try:
        destino.write_bytes(Path(origen).read_bytes())

    except OSError:
        return None

    return {**listo, "archivo": destino}


def soltar_relleno() -> dict[str, Any] | None:
    """Dice una muletilla ya preparada. Devuelve cuál dijo."""
    if not _rellenos_listos:
        return None

    elegido = random.choice(_rellenos_listos)

    motor_de_voz.emitir(elegido)

    return elegido


# Cómo se le llama. Un micrófono abierto oye la tele, a quien pasa por
# detrás y a quien habla por teléfono al lado, y todo eso llegaba como
# órdenes. Que haya que nombrarlo es lo único que separa de verdad "me
# hablan a mí" de "hay ruido".
NOMBRES = ("arquitecto", "arquitecta", "architect", "oye arquitecto")

# Después de contestar, un rato sin tener que volver a nombrarlo: en una
# conversación de verdad no se repite el nombre en cada frase.
SEGUIMIENTO = 25.0

# Cuándo respondió por última vez, para saber si sigue en conversación.
_ultima_vez = 0.0


def dirigido_a_mi(texto: str, ahora: float | None = None) -> tuple[bool, str]:
    """Si esa frase iba para él, y qué queda al quitarle el nombre.

    Devuelve ``(True, orden)`` o ``(False, "")``. Se le llama por su nombre
    para empezar; a partir de ahí, mientras la conversación siga viva, no
    hace falta repetirlo.
    """
    limpio = sin_adornos(texto)

    if not limpio:
        return (False, "")

    for nombre in NOMBRES:
        clave = sin_adornos(nombre)

        if not limpio.startswith(clave):
            continue

        # Se le quita el nombre y lo que suele venir pegado detrás.
        resto = limpio[len(clave) :].strip(" ,.:;")

        return (True, resto or texto)

    # Dentro de la conversación no hace falta nombrarlo. Fuera, sí.
    #
    # El cero es "todavía no ha contestado nunca", no "hace un instante".
    # Sin distinguirlo, al arrancar la resta daba cero y todo lo que se
    # oyera en la habitación pasaba por conversación en marcha.
    if _ultima_vez <= 0:
        return (False, "")

    if (ahora if ahora is not None else time.monotonic()) - _ultima_vez < SEGUIMIENTO:
        return (True, texto)

    return (False, "")


def atender(texto: str, project: str, si: bool) -> dict[str, Any]:
    """Interpreta una orden dicha en voz alta y prepara la respuesta.

    Separado del servidor a propósito: así se puede probar la conversación
    entera sin abrir un puerto ni un navegador.
    """
    from ai_architect.commands import pide

    orden = (texto or "").strip()[:LIMITE]

    if not orden:
        return {"respuesta": "No te entendí.", "dicho": "No te entendí.", "ms": 0}

    resultado = pide.run(project, frase=orden, si=si)

    respuesta = str(resultado.get("explanation") or resultado.get("error") or "")

    preparado = motor_de_voz.preparar(respuesta)

    global _ultimo_dicho, _ultima_vez

    _ultimo_dicho = str(preparado.get("texto", "") or respuesta)

    # La conversación sigue viva mientras conteste: durante un rato no hace
    # falta volver a llamarlo por su nombre.
    _ultima_vez = time.monotonic()

    return {
        "respuesta": respuesta,
        "dicho": preparado.get("texto", respuesta),
        "ms": int(preparado.get("segundos", 0) * 1000),
        "panel": resultado.get("panel"),
        "ventana": resultado.get("window", ""),
        "instantanea": bool(resultado.get("instant")),
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
            print(f"  · {muletilla.get('texto', '')}", flush=True)

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


class UnSoloDuenio(http.server.ThreadingHTTPServer):
    """Un servidor que **no** comparte el puerto.

    `HTTPServer` trae `allow_reuse_address = 1`, y en Windows eso no
    significa lo que en Unix: alli permite reciclar un puerto en TIME_WAIT,
    pero aqui deja que un segundo proceso se ate a un puerto que ya esta
    escuchando. Las dos instancias quedan vivas y el sistema reparte las
    conexiones entre ellas a capricho.

    Se vio en una prueba: con una conversacion abierta, levantar otro
    servidor no fallaba —como se esperaba— sino que se colaba, y las
    peticiones se iban a la conversacion de al lado. Poniendolo en False,
    el puerto ocupado se nota al instante y se puede decir.
    """

    allow_reuse_address = False


def _levantar(pagina: str, project: str, si: bool) -> tuple[Any, str]:
    class Manos(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - lo exige la librería
            ruta = self.path.split("?")[0]

            if ruta == "/respuesta":
                self._recoger()

                return

            if ruta not in ("/", "/index.html", "/rostro.html"):
                self.send_error(404)

                return

            self._responder(pagina.encode("utf-8"), "text/html; charset=utf-8")

        def do_POST(self) -> None:  # noqa: N802 - lo exige la librería
            ruta = self.path.split("?")[0]

            if ruta == "/oir":
                self._oir()

                return

            if ruta != "/orden":
                self.send_error(404)

                return

            try:
                largo = min(int(self.headers.get("Content-Length") or 0), LIMITE * 4)

                dicho = json.loads(self.rfile.read(largo) or b"{}").get("texto", "")

            except (ValueError, OSError):
                self.send_error(400)

                return

            print(f"  > {dicho}", flush=True)

            salida = atender(str(dicho), project, si)

            audio = salida.pop("_audio", None)

            self._responder(
                json.dumps(salida, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
            )

            # Después de contestar, no antes: la cara empieza a gesticular
            # al recibir la respuesta, y el sonido tiene que salir a la vez.
            if audio:
                threading.Thread(
                    target=motor_de_voz.emitir, args=(audio,), daemon=True
                ).start()

            print(f"  < {_resumen(salida['respuesta'])}", flush=True)

        def _oir(self) -> None:
            """Audio en crudo: se transcribe aquí y se trata como una orden."""
            from ai_architect.voz import escuchar

            largo = min(
                int(self.headers.get("Content-Length") or 0),
                escuchar.LIMITE_BYTES,
            )

            try:
                audio = self.rfile.read(largo)

            except OSError:
                self.send_error(400)

                return

            # Solo escucha la ultima pestana que se abrio. Abrir la cara
            # dos veces dejaba dos micros encendidos: mientras una hablaba,
            # la otra la oia por los altavoces y la mandaba de vuelta como
            # si fuera una orden. Se veian los ecos por duplicado.
            if self.headers.get("X-Turno") and self.headers["X-Turno"] != _turno:
                self._responder(
                    json.dumps({"detener": True}, ensure_ascii=False).encode("utf-8"),
                    "application/json; charset=utf-8",
                )

                return

            oido = escuchar.transcribir(audio)

            dicho = oido["texto"]

            if dicho and es_eco(dicho, _ultimo_dicho):
                # Se oyó a sí mismo por los altavoces. Ni se ejecuta ni se
                # contesta: contestar sería empezar una conversación consigo
                # mismo que no para hasta que alguien cierre la pestaña.
                print(f"  ~ (eco descartado) {dicho}", flush=True)

                self._responder(
                    json.dumps(
                        {"oido": "", "respuesta": "", "ms": 0, "error": "eco"},
                        ensure_ascii=False,
                    ).encode("utf-8"),
                    "application/json; charset=utf-8",
                )

                return

            if not dicho:
                # Ni se ejecuta ni se contesta. Lo que no se entendió no se
                # adivina, y soltar "no te entendí" a cada ruido de la
                # habitación acabaría siendo insoportable.
                self._responder(
                    json.dumps(
                        {"oido": "", "respuesta": "", "ms": 0, "error": oido["error"]},
                        ensure_ascii=False,
                    ).encode("utf-8"),
                    "application/json; charset=utf-8",
                )

                return

            # Solo lo que va dirigido a él. Un micrófono abierto oye la
            # tele, a quien pasa por detrás y a quien habla por teléfono al
            # lado, y todo eso llegaba como órdenes.
            para_mi, orden = dirigido_a_mi(dicho)

            if not para_mi:
                print(f"  · (no era para mí) {dicho}", flush=True)

                self._responder(
                    json.dumps(
                        {"oido": dicho, "ajeno": True, "respuesta": "", "ms": 0},
                        ensure_ascii=False,
                    ).encode("utf-8"),
                    "application/json; charset=utf-8",
                )

                return

            dicho = orden

            print(f"  > {dicho}", flush=True)

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
                args=(buzon, dicho, project, si),
                daemon=True,
            ).start()

            self._responder(
                json.dumps(
                    {"oido": dicho, "resguardo": resguardo}, ensure_ascii=False
                ).encode("utf-8"),
                "application/json; charset=utf-8",
            )

        def _recoger(self) -> None:
            """La respuesta, cuando esté. La página espera aquí colgada."""
            resguardo = ""

            if "?" in self.path:
                from urllib.parse import parse_qs

                resguardo = parse_qs(self.path.split("?", 1)[1]).get("r", [""])[0]

            buzon = _pendientes.pop(resguardo, None)

            if buzon is None:
                self.send_error(404)

                return

            try:
                salida = buzon.get(timeout=ESPERA_TRABAJO)

            except queue.Empty:
                salida = {
                    "respuesta": "Se me hizo largo y lo dejé.",
                    "dicho": "Se me hizo largo y lo dejé.",
                    "ms": 0,
                }

            sonido = salida.pop("_audio", None)

            self._responder(
                json.dumps(salida, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
            )

            print(f"  < {_resumen(salida.get('respuesta', ''))}", flush=True)

            if sonido:
                threading.Thread(
                    target=motor_de_voz.emitir, args=(sonido,), daemon=True
                ).start()

        def _responder(self, cuerpo: bytes, tipo: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(cuerpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            self.wfile.write(cuerpo)

        def log_message(self, *_: Any) -> None:
            """El servidor no ensucia la conversación con líneas de acceso."""

    try:
        servidor = UnSoloDuenio(("127.0.0.1", avatar.PUERTO), Manos)

    except OSError:
        return (None, "")

    servidor.daemon_threads = True

    return (servidor, f"http://127.0.0.1:{avatar.PUERTO}/")


def _resumen(respuesta: str) -> str:
    """El meollo de la respuesta, sin el saludo ni la despedida.

    Se imprimia la primera linea y la primera linea siempre es "Buenas
    tardes, Efrain": el registro de una conversacion entera decia lo mismo
    en todas las lineas y no servia para nada.
    """
    partes = [t.strip() for t in respuesta.split(chr(10) * 2) if t.strip()]

    return partes[1] if len(partes) > 2 else (partes[0] if partes else "")


def _apagar(servidor: Any) -> None:
    servidor.server_close()


def rostro() -> Path:
    return avatar.ROSTRO
