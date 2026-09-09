"""El servidor HTTP de la conversación: la página, el oído y las respuestas.

Separado de ``conversar`` para que el flujo se lea de una vez. Lo que
necesita de allí —el estado de la sesión, `atender_lo_oido`, la cola de
resguardos— lo lee en el momento (``c.``), no al importar: así el estado
sigue viviendo en un solo sitio y las pruebas que lo tocan lo ven.
"""

from __future__ import annotations

import http.server
import json
import queue
import threading
from typing import Any

from ai_architect.commands import avatar


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


def levantar(pagina: str, project: str, si: bool) -> tuple[Any, str]:
    from ai_architect.commands import conversar as c

    class Manos(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - lo exige la librería
            ruta = self.path.split("?")[0]

            if ruta == "/respuesta":
                self._recoger()

                return

            if ruta == "/progreso":
                desde = 0

                if "?" in self.path:
                    from urllib.parse import parse_qs

                    try:
                        desde = int(
                            parse_qs(self.path.split("?", 1)[1]).get("desde", ["0"])[0]
                        )

                    except ValueError:
                        desde = 0

                self._responder(
                    json.dumps(c.progreso_desde(desde), ensure_ascii=False).encode(
                        "utf-8"
                    ),
                    "application/json; charset=utf-8",
                )

                return

            if ruta == "/audio":
                datos = c.audio_preparado(self._parametro("t"))

                if datos is None:
                    self.send_error(404)

                    return

                self._responder(datos, "audio/wav")

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

            if ruta == "/permiso":
                self._permiso()

                return

            if ruta == "/dato":
                # Un dato que la cara pidió (token, clave…). Nunca se registra.
                try:
                    largo = min(int(self.headers.get("Content-Length") or 0), 8192)
                    cuerpo = json.loads(self.rfile.read(largo) or b"{}")
                    clave = str(cuerpo.get("clave", ""))
                    valor = str(cuerpo.get("valor", ""))

                except (ValueError, OSError, AttributeError):
                    self.send_error(400)

                    return

                self._enviar(c.recibir_dato(clave, valor))

                return

            if ruta == "/mirar":
                # Un fotograma de la cámara y la pregunta: se describe y se dice.
                try:
                    largo = min(int(self.headers.get("Content-Length") or 0), 6_000_000)
                    cuerpo = json.loads(self.rfile.read(largo) or b"{}")
                    imagen = str(cuerpo.get("imagen", ""))
                    pregunta = str(cuerpo.get("pregunta", ""))

                except (ValueError, OSError, AttributeError):
                    self.send_error(400)

                    return

                self._enviar(c.mirar_imagen(imagen, pregunta))

                return

            if ruta == "/sonar":
                # La página no pudo reproducir el audio: suena aquí.
                sono = c.sonar_aqui(self._parametro("t"))

                self._enviar({"sonando": sono})

                return

            if ruta != "/orden":
                self.send_error(404)

                return

            # La vía del reconocedor de Chrome: texto ya transcrito. Desde la
            # fase 4 va por el mismo camino que el audio: se contesta al
            # momento con un resguardo y el trabajo se hace aparte.
            try:
                largo = min(int(self.headers.get("Content-Length") or 0), c.LIMITE * 4)

                cuerpo = json.loads(self.rfile.read(largo) or b"{}")

                dicho = str(cuerpo.get("texto", ""))

            except (ValueError, OSError, AttributeError):
                self.send_error(400)

                return

            self._enviar(
                c.atender_lo_oido(
                    dicho.strip()[: c.LIMITE],
                    project,
                    si,
                    interrumpe=bool(cuerpo.get("interrumpe")),
                    error="no se entendió",
                )
            )

        def _parametro(self, nombre: str) -> str:
            if "?" not in self.path:
                return ""

            from urllib.parse import parse_qs

            return parse_qs(self.path.split("?", 1)[1]).get(nombre, [""])[0]

        def _enviar(self, salida: dict[str, Any]) -> None:
            """Responde en JSON; el audio, si es archivo, lo reproducirá la
            página; si no (voz de Windows), suena aquí después de contestar."""
            salida, sonido = c.entregar(salida)

            self._responder(
                json.dumps(salida, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
            )

            if salida.get("respuesta"):
                c._registro(f"  < {c._resumen(salida['respuesta'])}")

            if sonido:
                threading.Thread(
                    target=c.motor_de_voz.emitir, args=(sonido,), daemon=True
                ).start()

        def _permiso(self) -> None:
            """Los botones «Sí, hazlo» / «No» de la cara."""
            try:
                largo = min(int(self.headers.get("Content-Length") or 0), 4096)

                cuerpo = json.loads(self.rfile.read(largo) or b"{}")

                decision = "si" if cuerpo.get("decision") == "si" else "no"

            except (ValueError, OSError, AttributeError):
                self.send_error(400)

                return

            self._enviar(c.resolver_permiso(decision))

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
            if self.headers.get("X-Turno") and self.headers["X-Turno"] != c._turno:
                self._responder(
                    json.dumps({"detener": True}, ensure_ascii=False).encode("utf-8"),
                    "application/json; charset=utf-8",
                )

                return

            tipo = self.headers.get("Content-Type", "")

            oido = escuchar.transcribir(audio, ".wav" if "wav" in tipo else ".webm")

            # La huella de voz: se compara siempre que haya una aprendida.
            try:
                from ai_architect.voz import huella

                huella.comparar(audio)

            except Exception:  # noqa: BLE001 - la huella es un extra
                pass

            self._enviar(
                c.atender_lo_oido(
                    oido["texto"],
                    project,
                    si,
                    interrumpe=self.headers.get("X-Interrumpe") == "1",
                    error=oido["error"],
                )
            )

        def _recoger(self) -> None:
            """La respuesta, cuando esté. La página espera aquí colgada."""
            resguardo = self._parametro("r")

            buzon = c._pendientes.pop(resguardo, None)

            if buzon is None:
                self.send_error(404)

                return

            try:
                salida = buzon.get(timeout=c.ESPERA_TRABAJO)

            except queue.Empty:
                salida = {
                    "respuesta": "Se me hizo largo y lo dejé.",
                    "dicho": "Se me hizo largo y lo dejé.",
                    "ms": 0,
                }

            self._enviar(salida)

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


def apagar(servidor: Any) -> None:
    servidor.server_close()
