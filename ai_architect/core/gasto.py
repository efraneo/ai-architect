"""
=========================================================
Gasto

Cuánto lleva costado, y cuándo parar.
=========================================================

Hoy no hay tope. Una conversación larga encadena llamadas —el despachador,
el director, dos o tres especialistas, la voz, la transcripción— sin que
nadie avise. En una sesión de pruebas eso son céntimos; en un bucle mal
cerrado, o en manos de alguien que no sabe lo que cuesta cada frase, no.

**Lo que se cuenta y lo que no.** El precio real viene en la respuesta de
la API, pero cada proveedor lo devuelve a su manera y no todos lo
devuelven. Aquí se estima por caracteres, que es aproximado y **siempre por
arriba**: más vale avisar antes de tiempo que después. La cifra sirve para
frenar, no para facturar.

**Dónde se guarda.** En ``~/.ai_architect/gasto.json``, por día. Se borra
solo: lo de hace más de una semana no le importa a nadie y crecer sin
límite es otra forma de romperse.
"""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from typing import Any

from ai_architect.core.env_file import CARPETA_USUARIO


class TopeAlcanzado(RuntimeError):
    """Se llegó al límite de gasto.

    Tiene su propio tipo porque **no es un fallo**: el programa hizo justo
    lo que se le pidió. Decirle al usuario "el proveedor falló: llevo un
    dólar y ese es el tope" mezcla una avería con una decisión, y él no
    puede saber cuál de las dos le ha pasado.
    """


ARCHIVO = CARPETA_USUARIO / "gasto.json"

# Dólares por millón de caracteres, estimados por arriba desde el precio por
# millón de tokens y unos cuatro caracteres por token. No son la factura:
# son una cifra con la que decidir si seguir.
PRECIOS = {
    "gpt-5.5": (0.55, 4.40),
    "gpt-4o": (0.65, 2.60),
    "gpt-4o-mini": (0.04, 0.16),
    "gpt-5-mini": (0.07, 0.55),
}

POR_DEFECTO = (0.65, 2.60)

# Los topes. Se pueden subir con `AI_ARCHITECT_TOPE_DIA` y
# `AI_ARCHITECT_TOPE_SESION`, en dólares.
TOPE_DIA = 5.00

TOPE_SESION = 1.50

# A partir de aquí se avisa, antes de llegar al tope.
AVISO = 0.75

DIAS_QUE_SE_GUARDAN = 7

# Lo gastado en esta sesión. Muere con el proceso, a propósito: el tope de
# sesión existe para acotar un bucle, no para acumularse entre días.
_sesion = 0.0


def coste(modelo: str, entrada: str, salida: str) -> float:
    """Lo que costó esa llamada, estimado por arriba."""
    dentro, fuera = PRECIOS.get(modelo, POR_DEFECTO)

    return (len(entrada or "") * dentro + len(salida or "") * fuera) / 1_000_000


def registrar(modelo: str, entrada: str, salida: str) -> float:
    """Anota una llamada y devuelve lo que llevamos hoy."""
    global _sesion

    gastado = coste(modelo, entrada, salida)

    _sesion += gastado

    libro = _leer()

    hoy = date.today().isoformat()

    libro[hoy] = round(float(libro.get(hoy, 0.0)) + gastado, 6)

    _escribir(_podar(libro))

    return float(libro[hoy])


def hoy() -> float:
    return float(_leer().get(date.today().isoformat(), 0.0))


def sesion() -> float:
    return _sesion


def reiniciar_sesion() -> None:
    global _sesion

    _sesion = 0.0


def tope_dia() -> float:
    return _numero("AI_ARCHITECT_TOPE_DIA", TOPE_DIA)


def tope_sesion() -> float:
    return _numero("AI_ARCHITECT_TOPE_SESION", TOPE_SESION)


def permitido() -> tuple[bool, str]:
    """Si se puede seguir gastando, y por qué no si no.

    Se comprueba **antes** de llamar. Comprobarlo después sería contar el
    dinero que ya se fue.
    """
    if _sesion >= tope_sesion():
        return (
            False,
            f"Llevo {_dolares(_sesion)} en esta conversación y ese es el tope. "
            "Cierra y vuelve a abrir para seguir, o sube el límite con "
            "AI_ARCHITECT_TOPE_SESION.",
        )

    gastado = hoy()

    if gastado >= tope_dia():
        return (
            False,
            f"Hoy llevo {_dolares(gastado)} y ese es el tope del día. "
            "Mañana se reinicia, o súbelo con AI_ARCHITECT_TOPE_DIA.",
        )

    return (True, "")


def aviso() -> str:
    """Un aviso cuando queda poco, o vacío. Se dice una vez por tramo."""
    for cuanto, tope, donde in (
        (_sesion, tope_sesion(), "en esta conversación"),
        (hoy(), tope_dia(), "hoy"),
    ):
        if tope and cuanto / tope >= AVISO:
            return f"Aviso: llevo {_dolares(cuanto)} {donde}, de {_dolares(tope)}."

    return ""


def resumen() -> dict[str, Any]:
    return {
        "sesion": round(_sesion, 4),
        "hoy": round(hoy(), 4),
        "tope_sesion": tope_sesion(),
        "tope_dia": tope_dia(),
    }


# --- El libro ---------------------------------------------------------------


def _leer() -> dict[str, Any]:
    if not ARCHIVO.is_file():
        return {}

    try:
        datos = json.loads(ARCHIVO.read_text(encoding="utf-8"))

    except (OSError, ValueError):
        # Un libro ilegible no puede impedir trabajar. Se empieza de cero,
        # que como mucho deja pasar un día de gasto sin contar.
        return {}

    return dict(datos) if isinstance(datos, dict) else {}


def _escribir(libro: dict[str, Any]) -> None:
    try:
        ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVO.write_text(json.dumps(libro, indent=2), encoding="utf-8")

    except OSError:
        # No poder anotar el gasto no puede tumbar la respuesta. Se pierde
        # la cuenta, no la conversación.
        pass


def _podar(libro: dict[str, Any]) -> dict[str, Any]:
    limite = (date.today() - timedelta(days=DIAS_QUE_SE_GUARDAN)).isoformat()

    return {dia: valor for dia, valor in libro.items() if dia >= limite}


def _numero(variable: str, defecto: float) -> float:
    try:
        return float(os.getenv(variable) or defecto)

    except ValueError:
        return defecto


def _dolares(cuanto: float) -> str:
    """El importe como se dice en voz alta, no como se imprime."""
    if cuanto < 0.01:
        return "menos de un centavo"

    return f"{cuanto:.2f} dólares".replace(".", ",")
