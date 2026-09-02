"""
=========================================================
Respuestas

Lo que no hace falta preguntarle a un modelo.
=========================================================

"¿Qué hora es?" tardaba tres segundos: la frase iba a un modelo grande,
el modelo decidía que no era ninguna tarea del repositorio y redactaba una
respuesta. Tres segundos, una llamada de pago, y para algo que está en
``datetime.now()``.

Aquí se resuelven en el sitio las preguntas que no necesitan a nadie: la
hora, la fecha, un saludo, quién es, qué sabe hacer, y las órdenes sobre
la ventana flotante. Son instantáneas y gratis.

La regla para meter algo aquí es estrecha a propósito: **la respuesta tiene
que estar completamente determinada por la frase y por el reloj**. En
cuanto haya que interpretar o mirar el repositorio, es cosa del modelo. Un
atajo que adivina mal es peor que tres segundos de espera.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from ai_architect.core import perfil
from ai_architect.core.texto import contiene, sin_adornos

# --- La hora ----------------------------------------------------------------

HORA = ("que hora", "hora es", "horas son", "que horas", "dime la hora", "la hora")

FECHA = (
    "que dia es",
    "que fecha",
    "en que fecha",
    "dia de hoy",
    "que dia estamos",
    "a cuantos estamos",
)

# --- La ventana flotante ----------------------------------------------------

AMPLIAR = (
    "amplia",
    "ampliala",
    "agranda",
    "agrandala",
    "expande",
    "expandela",
    "maximiza",
    "hazla grande",
    "mas grande",
    "pantalla completa",
    "abrela",
)

REDUCIR = (
    "reduce",
    "reducela",
    "minimiza",
    "achica",
    "hazla pequena",
    "mas pequena",
    "encogela",
)

CERRAR_VENTANA = (
    "cierra la ventana",
    "cierrala",
    "quita la ventana",
    "quitala",
    "cierra el panel",
    "borra la ventana",
)

# --- Cortesía ---------------------------------------------------------------

SALUDOS = ("hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buenas")

GRACIAS = ("gracias", "muchas gracias", "te lo agradezco", "genial", "perfecto")

QUIEN = ("quien eres", "como te llamas", "quien te hizo", "quien es tu creador")

QUE_SABES = (
    "que sabes hacer",
    "que puedes hacer",
    "en que me puedes ayudar",
    "que haces",
    "para que sirves",
)


# --- El cambio de divisas ---------------------------------------------------
#
# "¿A cuánto está el dólar?" es una pregunta razonable y el modelo no puede
# contestarla: no sabe la cotización de hoy, y lo honrado por su parte es
# decir que no. Pero mandar a alguien a buscarlo en una web cuando el dato
# está a una petición de distancia tampoco sirve de nada.

CAMBIO = ("a cuanto esta", "cuanto esta", "valor del", "cotizacion", "cambio del")

MONEDAS = {
    "dolar": "USD",
    "dolares": "USD",
    "euro": "EUR",
    "euros": "EUR",
    "libra": "GBP",
    "libras": "GBP",
    "real": "BRL",
    "reales": "BRL",
    "yen": "JPY",
    "peso mexicano": "MXN",
    "peso argentino": "ARS",
    "peso chileno": "CLP",
    "peso colombiano": "COP",
}

# Contra qué se compara si no lo dice. Se puede cambiar con la variable
# `AI_ARCHITECT_MONEDA`; el valor por defecto es el peso colombiano porque
# es la moneda de quien pregunta.
DESTINOS = {
    "peso colombiano": "COP",
    "pesos colombianos": "COP",
    "peso mexicano": "MXN",
    "pesos mexicanos": "MXN",
    "peso argentino": "ARS",
    "peso chileno": "CLP",
    "euro": "EUR",
    "euros": "EUR",
    "dolar": "USD",
    "dolares": "USD",
}

FUENTE = "https://open.er-api.com/v6/latest/"

# Si tarda más que esto, no compensa: se dice que no se pudo y a otra cosa.
TIEMPO_LIMITE = 5


def responder(frase: str, ahora: datetime | None = None) -> dict[str, Any] | None:
    """La respuesta inmediata, o ``None`` si esto hay que pensarlo.

    Devolver ``None`` no es un fallo: es lo normal. Aquí solo caen las
    preguntas cuya respuesta ya está en la máquina o a una petición.
    """
    limpia = sin_adornos(frase)

    if not limpia:
        return None

    for prueba in (
        _ventana,
        _hora,
        _fecha,
        _divisa,
        _quien,
        _que_sabes,
        _cortesia,
    ):
        salida = prueba(limpia, ahora)

        if salida is not None:
            return salida

    return None


def _divisa(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    if not contiene(limpia, *CAMBIO):
        return None

    # La más larga primero: "peso mexicano" antes que "peso".
    origen = next(
        (
            codigo
            for nombre, codigo in sorted(MONEDAS.items(), key=lambda p: -len(p[0]))
            if nombre in limpia
        ),
        "",
    )

    if not origen:
        return None

    destino = next(
        (
            codigo
            for nombre, codigo in sorted(DESTINOS.items(), key=lambda p: -len(p[0]))
            if f" en {nombre}" in f" {limpia}" or f"a {nombre}" in limpia
        ),
        os.getenv("AI_ARCHITECT_MONEDA", "COP"),
    )

    if destino == origen:
        destino = "COP" if origen != "COP" else "USD"

    valor, fecha = _cotizacion(origen, destino)

    if valor is None:
        # Sin red no se inventa una cifra. Una cotización inventada es peor
        # que no contestar, porque parece buena.
        return {
            "respuesta": (
                "No pude consultar la cotización ahora mismo. "
                "Puede ser que no haya internet."
            )
        }

    return {
        "respuesta": f"Un {_como_se_dice(origen)} está en {_redondo(valor)} {destino}.",
        "panel": {
            "tipo": "cambio",
            "titulo": f"{origen} → {destino}",
            "valor": round(valor, 2),
            "par": f"1 {origen} = {round(valor, 2)} {destino}",
            "fecha": fecha,
        },
    }


def _cotizacion(origen: str, destino: str) -> tuple[float | None, str]:
    """La cotización de hoy. Sin clave y sin dependencias nuevas."""
    import json
    import urllib.request

    try:
        with urllib.request.urlopen(FUENTE + origen, timeout=TIEMPO_LIMITE) as red:
            datos = json.loads(red.read().decode("utf-8"))

    except Exception:  # noqa: BLE001 - sin red se dice, no se revienta
        return (None, "")

    tasa = (datos.get("rates") or {}).get(destino)

    if not isinstance(tasa, (int, float)):
        return (None, "")

    return (float(tasa), str(datos.get("time_last_update_utc", ""))[:16])


def _como_se_dice(codigo: str) -> str:
    return {
        "USD": "dólar",
        "EUR": "euro",
        "GBP": "libra",
        "BRL": "real",
        "JPY": "yen",
        "MXN": "peso mexicano",
        "COP": "peso colombiano",
        "ARS": "peso argentino",
        "CLP": "peso chileno",
    }.get(codigo, codigo)


def _redondo(valor: float) -> str:
    """La cifra como se dice, no como se imprime.

    "4109.5" en voz alta es un galimatías; "4.110" se entiende.
    """
    if valor >= 100:
        return f"{valor:,.0f}".replace(",", ".")

    return f"{valor:.2f}".replace(".", ",")


# --- Cada atajo -------------------------------------------------------------


def _hora(limpia: str, ahora: datetime | None) -> dict[str, Any] | None:
    if not contiene(limpia, *HORA):
        return None

    momento = ahora or datetime.now()

    return {
        "respuesta": f"Son las {_en_palabras(momento)}.",
        # El reloj se queda en pantalla: preguntar la hora suele ser mirar
        # el reloj, no oírla una vez y olvidarla.
        "panel": {
            "tipo": "reloj",
            "titulo": "Hora",
            "hora": momento.strftime("%H:%M"),
            "segundos": momento.strftime("%S"),
            "fecha": _fecha_larga(momento),
        },
    }


def _fecha(limpia: str, ahora: datetime | None) -> dict[str, Any] | None:
    if not contiene(limpia, *FECHA):
        return None

    momento = ahora or datetime.now()

    return {
        "respuesta": f"Hoy es {_fecha_larga(momento)}.",
        "panel": {
            "tipo": "reloj",
            "titulo": "Fecha",
            "hora": momento.strftime("%H:%M"),
            "segundos": momento.strftime("%S"),
            "fecha": _fecha_larga(momento),
        },
    }


def _ventana(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    """Órdenes sobre la ventana flotante. Van primero y por buenas razones.

    "amplíala" no es una pregunta sobre el repositorio, y mandarla a un
    modelo para que decida eso son dos segundos de espera para mover una
    caja que ya está en pantalla.
    """
    if contiene(limpia, *CERRAR_VENTANA):
        return {"respuesta": "Cerrada.", "ventana": "cerrar"}

    if contiene(limpia, *AMPLIAR):
        return {"respuesta": "Ahí la tienes.", "ventana": "ampliar"}

    if contiene(limpia, *REDUCIR):
        return {"respuesta": "Listo.", "ventana": "reducir"}

    return None


def _quien(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    if not contiene(limpia, *QUIEN):
        return None

    return {
        "respuesta": (
            f"Soy el arquitecto. Me hizo {perfil.quien_te_hizo()}, "
            "y trabajo sobre tu repositorio."
        )
    }


def _que_sabes(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    if not contiene(limpia, *QUE_SABES):
        return None

    return {
        "respuesta": (
            "Puedo revisar el código y puntuarlo, pasarle los agentes en busca "
            "de problemas, analizar la estructura, comprobar el entorno, armar "
            "el changelog y proponer mejoras. Dímelo como quieras."
        )
    }


def _cortesia(limpia: str, ahora: datetime | None) -> dict[str, Any] | None:
    """Solo si la frase es **nada más que** el saludo.

    "hola" se contesta al momento; "hola, revisa el proyecto" no, porque
    ahí lo que importa es lo segundo. Por eso se mide la frase entera en
    vez de buscar la palabra dentro.
    """
    palabras = limpia.split()

    if len(palabras) > 4:
        return None

    if contiene(limpia, *GRACIAS):
        return {"respuesta": "A ti."}

    if any(limpia.startswith(sin_adornos(s)) for s in SALUDOS):
        return {"respuesta": f"{perfil.saludo(ahora)}, {perfil.como_llamarte()}."}

    return None


# --- Decir la hora como se dice ---------------------------------------------


def _en_palabras(momento: datetime) -> str:
    """La hora dicha, no leída.

    "15:42" en voz alta suena a marcador. Se dice como se diría.
    """
    hora = momento.hour % 12 or 12
    minuto = momento.minute

    franja = (
        "de la mañana"
        if momento.hour < 12
        else "de la tarde" if momento.hour < 20 else "de la noche"
    )

    if minuto == 0:
        cuerpo = f"{hora} en punto"

    elif minuto == 15:
        cuerpo = f"{hora} y cuarto"

    elif minuto == 30:
        cuerpo = f"{hora} y media"

    elif minuto == 45:
        cuerpo = f"{(hora % 12) + 1} menos cuarto"

    else:
        cuerpo = f"{hora} y {minuto}"

    return f"{cuerpo} {franja}"


def _fecha_larga(momento: datetime) -> str:
    """El día en español, sin depender del locale del sistema."""
    from ai_architect.commands.pide import DIAS, MESES

    return (
        f"{DIAS[momento.weekday()]} {momento.day} "
        f"de {MESES[momento.month - 1]} de {momento.year}"
    )
