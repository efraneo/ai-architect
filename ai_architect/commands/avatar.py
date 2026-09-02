"""
=========================================================
Avatar

La cara que responde.
=========================================================

Un rostro de nebulosa en el navegador, servido desde ``127.0.0.1``.

**Por qué un servidor y no un archivo.** La primera versión abría el HTML
con ``file://`` y pasaba la duración del audio en la URL. No funcionó, y el
motivo no se ve en el código: en Windows ``webbrowser`` acaba llamando a
``os.startfile``, el shell resuelve el ``file:`` como una **ruta**, y ahí
el ``?`` no es un carácter válido. La query se perdía entera. La cara se
abría, giraba con el ratón, y nunca se enteraba de que tenía que hablar.

Servirlo por HTTP arregla eso, y abre la puerta a lo otro: ``getUserMedia``
—la cámara— exige un contexto seguro, y ``file://`` no lo es. ``localhost``
sí. Sin servidor no hay forma de que la cara te siga.

**Cuándo suena.** El navegador no puede reproducir el audio él mismo: las
políticas de autoarranque lo bloquean sin un clic previo. Lo pone Python,
y para saber cuándo ya no se adivina — el servidor espera a que la página
se pida de verdad, y solo entonces empieza a sonar.
"""

from __future__ import annotations

import http.server
import json
import socket
import tempfile
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

from ai_architect.core import perfil
from ai_architect.voz import hablar as motor_de_voz

ROSTRO = Path(__file__).resolve().parent.parent / "avatar" / "rostro.html"

# Donde el HTML espera que se le inyecten los datos de esta sesión.
MARCA = "/* __DATOS__ */"

# Fijo a propósito: con el mismo origen el navegador recuerda el permiso
# de cámara y reutiliza la pestaña en vez de abrir una nueva cada vez.
PUERTO = 8731

# Lo que se le da a la página para pintar el primer fotograma después de
# haberla pedido. Ya no es una adivinanza sobre cuánto tarda en arrancar
# el navegador: a estas alturas el navegador ya está.
RENDER = 0.45

# Si en ese tiempo nadie pide la página, algo va mal y se sigue sin ella.
ESPERA_MAXIMA = 20.0


def run(
    decir: str = "",
    abrir: bool = True,
    esperar: float | None = None,
    servir: bool = True,
) -> dict[str, Any]:
    """Muestra la cara. Con ``decir``, además habla y gesticula."""
    if not ROSTRO.is_file():
        return {"success": False, "error": f"no encuentro el rostro en {ROSTRO}"}

    preparado = motor_de_voz.preparar(decir) if decir.strip() else None

    pagina = _componer(decir, preparado)

    servidor, url, servido = (None, "", None)

    if servir:
        servidor, url, servido = _levantar(pagina)

    if servidor is None:
        # Sin servidor no hay cámara, pero la cara sigue saliendo.
        url = _archivo_suelto(pagina).as_uri()

    if abrir:
        webbrowser.open(url)

        if servido is not None:
            servido.wait(ESPERA_MAXIMA)

        if preparado:
            time.sleep(esperar if esperar is not None else RENDER)

    hablado = motor_de_voz.emitir(preparado) if preparado else False

    if servidor is not None:
        _apagar(servidor)

    return {
        "success": True,
        "url": url,
        "served": servidor is not None,
        "spoke": hablado,
        "engine": (preparado or {}).get("motor", ""),
        "seconds": round((preparado or {}).get("segundos", 0.0), 2),
        "explanation": _explicar(decir, preparado, hablado, servidor is not None),
    }


# --- La página --------------------------------------------------------------


def _componer(decir: str, preparado: dict[str, Any] | None) -> str:
    """El HTML con los datos de esta sesión dentro.

    Inyectados, no en la URL: ver el porqué en la cabecera del módulo.
    """
    datos = {
        "ms": int((preparado or {}).get("segundos", 0) * 1000),
        # El texto va porque la boca sigue las sílabas de verdad. Con solo
        # la duración habría que fingir un ritmo, y se nota.
        "texto": (preparado or {}).get("texto", "") or decir.strip(),
        "retraso": 120,
    }

    cuerpo = ROSTRO.read_text(encoding="utf-8")

    return cuerpo.replace(
        MARCA,
        "window.DATOS_ARQUITECTO = " + json.dumps(datos, ensure_ascii=False) + ";",
        1,
    )


def _archivo_suelto(pagina: str) -> Path:
    destino = Path(tempfile.gettempdir()) / "arquitecto-rostro.html"

    destino.write_text(pagina, encoding="utf-8")

    return destino


# --- El servidor ------------------------------------------------------------


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


def _levantar(pagina: str) -> tuple[Any, str, threading.Event | None]:
    """Sirve la página en localhost. Devuelve ``(None, "", None)`` si no puede."""
    servido = threading.Event()

    class Manos(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - lo exige la librería
            if self.path.split("?")[0] not in ("/", "/index.html", "/rostro.html"):
                self.send_error(404)

                return

            cuerpo = pagina.encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            # Sin esto el navegador reutiliza la página de la vez anterior,
            # con la frase anterior dentro.
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            self.wfile.write(cuerpo)

            servido.set()

        def log_message(self, *_: Any) -> None:
            """El servidor no escribe en la terminal del usuario."""

    try:
        servidor = UnSoloDuenio(("127.0.0.1", PUERTO), Manos)

    except OSError:
        return (None, "", None)

    servidor.daemon_threads = True

    threading.Thread(target=servidor.serve_forever, daemon=True).start()

    return (servidor, f"http://127.0.0.1:{PUERTO}/", servido)


def _apagar(servidor: Any) -> None:
    """Se cierra en cuanto la página está cargada: ya no lo necesita."""
    threading.Thread(target=servidor.shutdown, daemon=True).start()

    servidor.server_close()


def puerto_libre() -> bool:
    """Si el puerto está tomado, esta vez se irá por ``file://`` y sin cámara."""
    with socket.socket() as prueba:
        return prueba.connect_ex(("127.0.0.1", PUERTO)) != 0


# --- Lo que se dice en la terminal ------------------------------------------


def _explicar(
    decir: str,
    preparado: dict[str, Any] | None,
    hablado: bool,
    servido: bool,
) -> str:
    partes = [f"{perfil.encabezar()} Abrí el rostro en el navegador."]

    if not servido:
        partes.append(
            f"El puerto {PUERTO} estaba ocupado, así que va por archivo: "
            "esta vez sin cámara."
        )

    if not decir.strip():
        partes.append("Pulsa espacio para que hable.")

    elif hablado:
        segundos = (preparado or {}).get("segundos", 0.0)

        partes.append(f"Dije lo que me pediste en {segundos:.1f} s.")

    else:
        motivo = (preparado or {}).get("motivo") or "no hay ninguna voz disponible"

        partes.append(f"La cara está, pero no pude hablar: {motivo}.")

    return " ".join(partes)
