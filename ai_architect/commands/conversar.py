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

**Lo que conviene saber.** La transcripción la hace Chrome, y Chrome manda
el audio a los servidores de Google. No es local. La alternativa sería
grabar en el navegador y transcribir con Whisper desde Python: más privado
frente a Google —aunque el audio acabe igualmente en OpenAI— y de pago.

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
import webbrowser
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
        f"  La transcripción la hace Chrome, y va por los servidores de Google.\n\n"
        f"  Ctrl+C para terminar.\n"
    )

    print(aviso)

    if servir_para_siempre:
        try:
            servidor.serve_forever()

        except KeyboardInterrupt:
            print(f"\n{perfil.despedir()}")

        finally:
            _apagar(servidor)

    return {"success": True, "url": url, "authorised": si}


def _componer(project: str) -> str:
    datos = {"ms": 0, "texto": "", "modo": "conversacion", "proyecto": project}

    return avatar.ROSTRO.read_text(encoding="utf-8").replace(
        avatar.MARCA,
        "window.DATOS_ARQUITECTO = " + json.dumps(datos, ensure_ascii=False) + ";",
        1,
    )


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

    return {
        "respuesta": respuesta,
        "dicho": preparado.get("texto", respuesta),
        "ms": int(preparado.get("segundos", 0) * 1000),
        "_audio": preparado,
    }


def _levantar(pagina: str, project: str, si: bool) -> tuple[Any, str]:
    class Manos(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - lo exige la librería
            if self.path.split("?")[0] not in ("/", "/index.html", "/rostro.html"):
                self.send_error(404)

                return

            self._responder(pagina.encode("utf-8"), "text/html; charset=utf-8")

        def do_POST(self) -> None:  # noqa: N802 - lo exige la librería
            if self.path.split("?")[0] != "/orden":
                self.send_error(404)

                return

            try:
                largo = min(int(self.headers.get("Content-Length") or 0), LIMITE * 4)

                dicho = json.loads(self.rfile.read(largo) or b"{}").get("texto", "")

            except (ValueError, OSError):
                self.send_error(400)

                return

            print(f"  > {dicho}")

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

            print(f"  < {salida['respuesta'].splitlines()[0]}")

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
        servidor = http.server.ThreadingHTTPServer(("127.0.0.1", avatar.PUERTO), Manos)

    except OSError:
        return (None, "")

    servidor.daemon_threads = True

    return (servidor, f"http://127.0.0.1:{avatar.PUERTO}/")


def _apagar(servidor: Any) -> None:
    servidor.server_close()


def rostro() -> Path:
    return avatar.ROSTRO
