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


def responder(frase: str, ahora: datetime | None = None) -> dict[str, Any] | None:
    """La respuesta inmediata, o ``None`` si esto hay que pensarlo.

    Devolver ``None`` no es un fallo: es lo normal. Aquí solo caen las
    preguntas cuya respuesta ya está en la máquina.
    """
    limpia = sin_adornos(frase)

    if not limpia:
        return None

    for prueba in (_ventana, _hora, _fecha, _quien, _que_sabes, _cortesia):
        salida = prueba(limpia, ahora)

        if salida is not None:
            return salida

    return None


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
