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
import threading
import unicodedata
import webbrowser
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from ai_architect.commands import avatar
from ai_architect.core import perfil
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

    webbrowser.open(url)

    aviso = (
        f"{perfil.encabezar()} Te escucho.\n\n"
        f"  Habla en voz alta. Lo que entienda te lo escribo en la pantalla,\n"
        f"  para que si me equivoco lo veas al momento.\n\n"
        f"  Órdenes que tocan archivos: {'autorizadas' if si else 'NO autorizadas'}"
        f"{'' if si else ' (arranca con --si para permitirlas)'}.\n"
        f"  Te oye: {_quien_oye()}\n\n"
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


def _componer(project: str) -> str:
    from ai_architect.voz import escuchar

    datos = {
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


def _sin_adornos(texto: str) -> str:
    """El texto reducido a lo comparable: sin tildes, signos ni mayusculas."""
    plano = unicodedata.normalize("NFKD", texto.lower())

    letras = [c for c in plano if c.isalnum() or c.isspace()]

    return " ".join("".join(letras).split())


def es_eco(oido: str, dicho: str) -> bool:
    """Si lo que se acaba de oir es la propia voz saliendo por los altavoces.

    El navegador ya se tapa los oidos mientras habla, pero eso depende de
    que su reloj y el del audio vayan a la par —y no van—, y de que no haya
    dos pestanas abiertas escuchando a la vez. Aqui se comprueba lo unico
    que no enga:na: si lo oido es lo que se acaba de decir. Aunque llegue
    tarde, aunque llegue por otra pestana.
    """
    a = _sin_adornos(oido)
    b = _sin_adornos(dicho)

    if not a or not b:
        return False

    # Con menos de tres palabras no se puede juzgar: "si", "ya" o "para"
    # son ordenes legitimas y aparecen en cualquier respuesta.
    if len(a.split()) < 3:
        return False

    if a in b:
        return True

    return SequenceMatcher(None, a, b).ratio() > 0.62


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

    global _ultimo_dicho

    _ultimo_dicho = str(preparado.get("texto", "") or respuesta)

    return {
        "respuesta": respuesta,
        "dicho": preparado.get("texto", respuesta),
        "ms": int(preparado.get("segundos", 0) * 1000),
        "_audio": preparado,
    }


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
            if self.path.split("?")[0] not in ("/", "/index.html", "/rostro.html"):
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

            print(f"  < {salida['respuesta'].splitlines()[0]}", flush=True)

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

            print(f"  > {dicho}", flush=True)

            salida = atender(dicho, project, si)

            salida["oido"] = dicho

            sonido = salida.pop("_audio", None)

            self._responder(
                json.dumps(salida, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
            )

            if sonido:
                threading.Thread(
                    target=motor_de_voz.emitir, args=(sonido,), daemon=True
                ).start()

            print(f"  < {salida['respuesta'].splitlines()[0]}", flush=True)

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


def _apagar(servidor: Any) -> None:
    servidor.server_close()


def rostro() -> Path:
    return avatar.ROSTRO
