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
import re
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

    # La memoria va antes y con la frase original: lo que se apunta se guarda
    # tal como se dijo, con mayúsculas y tildes, no la versión limpia.
    recordado = _memoria(limpia, frase)

    if recordado is not None:
        return recordado

    # La palabra maestra: solo ella arranca una reparación o una reconstrucción.
    maestra = _adelante(limpia)

    if maestra is not None:
        return maestra

    # «Llama a Juan», «pon música», «bloquea el celular»: al teléfono, ya.
    telefono = _celular(limpia, frase)

    if telefono is not None:
        return telefono

    for prueba in (
        _ventana_app,
        _ventana,
        _cerrar,
        _reposo,
        _queja,
        _mejora,
        _abrir,
        _calculo,
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


# --- La memoria -------------------------------------------------------------

RECUERDA = (
    "recuerda que",
    "recuerdame que",
    "acuerdate de que",
    "acuerdate que",
    "anota que",
    "apunta que",
    # En la prueba real: «guarda en tu memoria que no me debes…» se fue al
    # especialista de seguridad en vez de a la memoria.
    "guarda en tu memoria que",
    "guarda en memoria que",
    "guarda en la memoria que",
    "memoriza que",
    "ten en cuenta que",
    "ten presente que",
    "no olvides que",
)

REPARATE = (
    "reparate",
    "arreglate",
    "repara tu codigo",
    "arregla tu codigo",
    "repara tus errores",
    "arreglate a ti mismo",
    "corrigete",
)
QUE_SABES_DE_MI = (
    "que sabes de mi",
    "que recuerdas de mi",
    "que recuerdas",
    "que sabes sobre mi",
    "tu memoria",
)
OLVIDA = ("olvida todo", "olvidalo todo", "borra tu memoria", "borra la memoria")


CONECTAR_CELULAR = (
    "conectate al celular",
    "conecta el celular",
    "configura el celular",
    "configura telegram",
    "conecta telegram",
)
CONECTAR_CORREO = ("configura el correo", "conecta el correo", "configura mi correo")


def _adelante(limpia: str) -> dict[str, Any] | None:
    """«Adelante» es la palabra maestra: repara o reconstruye lo que espera, y nada más.
    También «conéctate al celular» / «configura el correo» arrancan la configuración guiada.
    """
    from ai_architect import autoreparacion

    if autoreparacion.es_palabra_maestra(limpia):
        from ai_architect.commands import conversar

        return {"respuesta": autoreparacion.adelante(avisar=conversar.decir_proactivo)}

    if limpia in REPARATE:
        averia = autoreparacion.pendiente()

        if averia is None:
            return {
                "respuesta": (
                    "No tengo ninguna avería apuntada. Cuando algo falle en mi código te "
                    "lo diré, y lo reparo solo si me dices «adelante»."
                )
            }

        return {
            "respuesta": (
                f"Tengo una avería pendiente en «{averia['comando']}». "
                "Si dices «adelante», la reviso, la corrijo y corro mis pruebas."
            )
        }

    if limpia in CONECTAR_CELULAR:
        from ai_architect.canales import asistente

        return asistente.empezar("telegram")

    if limpia in CONECTAR_CORREO:
        from ai_architect.canales import asistente

        return asistente.empezar("correo")

    return None


def _celular(limpia: str, original: str) -> dict[str, Any] | None:
    """Las órdenes al celular se resuelven aquí, sin modelo: van por Telegram a
    una automatización del teléfono (docs/CELULAR.md). Llamar y mandar SMS
    quedan esperando un «sí»; lo demás sale al momento."""
    from ai_architect.canales import celular

    entendido = celular.entender(original)

    if entendido is None:
        return None

    accion, argumento = entendido

    if accion == "desbloquear":
        return {
            "respuesta": (
                "Eso no lo permite el teléfono: desbloquear solo se puede con tu cara, "
                "tu huella o tu clave. Puedo bloquearlo, llamar, poner música o abrir apps."
            )
        }

    from ai_architect.canales import asistente, telegram

    if not telegram.configurado():
        # Sin bot no hay celular: se configura ahora, pidiendo lo que falte, y
        # la orden se retoma sola en cuanto quede conectado.
        return asistente.empezar("telegram", original)

    if accion in celular.CON_PERMISO:
        from pathlib import Path

        from ai_architect.commands import pendientes

        numero = celular.numero_de(argumento) if accion == "llamar" else argumento
        pendiente = pendientes.encolar(
            Path.cwd(),
            "celular_llamar",
            {"accion": accion, "argumento": numero},
            original,
        )
        que = (
            f"¿Llamo a {argumento}"
            + (f" ({numero})" if numero != argumento else "")
            + "?"
        )

        if accion == "mensaje":
            que = f"¿Mando el mensaje a {argumento.split('|', 1)[0]}?"

        return {
            "respuesta": que + " Di sí o no.",
            "pending": [pendiente.description],
            "pending_ids": [pendiente.id],
            "pregunta_permiso": True,
        }

    salida = celular.ordenar(accion, argumento)

    if not salida.get("ok"):
        return {"respuesta": f"No pude mandarlo al celular: {salida.get('error')}"}

    dicho = {
        "colgar": "Colgado.",
        "bloquear": "Bloqueado.",
        "pausar": "Pausada.",
        "reanudar": "Sigue.",
        "siguiente": "Siguiente.",
        "anterior": "Anterior.",
        "sonar": "Sonando.",
    }.get(
        accion,
        f"Mandado: {celular.ACCIONES[accion]}"
        + (f" ({argumento})." if argumento else "."),
    )

    return {"respuesta": dicho}


def _memoria(limpia: str, original: str) -> dict[str, Any] | None:
    """«Recuerda que…», «qué sabes de mí» y «olvida todo» se resuelven sin modelo.

    Van a la memoria de hechos a largo plazo (``ai_architect.agente.memoria``): lo que se
    dice con «recuerda que» entra como hecho de confianza y sale en los prompts siguientes.
    """
    from ai_architect.agente import memoria
    from ai_architect.commands.memoria import run as memoria_run

    if limpia.startswith(RECUERDA) or limpia in OLVIDA:
        _quiza_un_contacto(original)

        salida = memoria_run(original if limpia.startswith(RECUERDA) else limpia)
        return {"respuesta": salida["explanation"], "panel": salida.get("panel")}

    if limpia in QUE_SABES_DE_MI:
        hechos = memoria.hechos()
        if not hechos:
            return {
                "respuesta": "Todavía no sé nada de ti. Dime «recuerda que…» y lo apunto."
            }
        cuerpo = "\n".join(f"{i + 1}. {h.text}" for i, h in enumerate(hechos))
        ultimos = "; ".join(h.text for h in hechos[-5:])
        return {
            "respuesta": f"Recuerdo {len(hechos)} cosa(s) de ti: {ultimos}.",
            "panel": {
                "tipo": "texto",
                "titulo": "Memoria de Architect",
                "cuerpo": cuerpo,
            },
        }

    return None


CONTACTO = re.compile(
    r"(?:numero|telefono|celular|movil)\s+de\s+(?P<quien>[^,]+?)\s+es\s+(?:el\s+)?(?P<numero>\+?[\d][\d ]{5,})",
    re.IGNORECASE,
)


def _quiza_un_contacto(original: str) -> None:
    """«El número de Juan es 300…» también va a la agenda del celular."""
    m = CONTACTO.search(sin_adornos(original).replace("+", " +"))

    if not m:
        return

    from ai_architect.canales import celular

    celular.guardar_contacto(m["quien"], m["numero"])


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


VENTANA_APP = re.compile(
    r"^(?:architect,?\s+)?(?P<que>maximiza|maximizar|minimiza|minimizar|restaura|restaurar|pantalla completa)"
    r"(?:\s+(?:la\s+)?ventana)?(?:\s+(?:de architect|del programa|de la presentacion|la presentacion))?$"
)


def _ventana_app(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    """«Maximiza ventana» / «minimiza ventana»: la ventana de Architect (la
    presentación), no el panel flotante de dentro."""
    m = VENTANA_APP.match(limpia)

    if m is None:
        return None

    accion = {
        "maximiza": "maximizar",
        "maximizar": "maximizar",
        "minimiza": "minimizar",
        "minimizar": "minimizar",
        "restaura": "restaurar",
        "restaurar": "restaurar",
        "pantalla completa": "pantalla_completa",
    }[m["que"]]

    return {
        "respuesta": {
            "maximizar": "Maximizada.",
            "minimizar": "Minimizada.",
            "restaurar": "Restaurada.",
            "pantalla_completa": "Pantalla completa.",
        }[accion],
        "ventana_app": accion,
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


CERRARSE = (
    "cierra architect",
    "cierra arquitecto",
    "cierrate",
    "apagate",
    "apaga architect",
    "termina tu ejecucion",
    "termina la ejecucion",
    "termina",
    "cierra",
    "cierra la sesion",
    "cierra el programa",
    "adios",
    "hasta luego",
    "hasta manana",
    "chao",
    "nos vemos",
    "buenas noches architect",
    "cerrar",
    "cierra ya",
    "cierrate ya",
    "no cierra",
    "no cierrate",
    "apagate ya",
    "ya puedes cerrar",
    "despidete",
    "despidete ya",
    "despidete y cierra",
    "puedes cerrar",
)

REPOSO = (
    "quedate en reposo",
    "ponte en reposo",
    "reposo",
    "descansa",
    "duerme",
    "duermete",
    "transformate en nebulosa",
    "vuelve a la nebulosa",
    "hazte nebulosa",
    "deshazte",
)

QUEJA = (
    "eso esta mal",
    "esta mal",
    "no lo hiciste",
    "no lo haces",
    "no lo has hecho",
    "te equivocaste",
    "te has equivocado",
    "no funciona",
    "no me hiciste caso",
    "lo hiciste mal",
    "no era eso",
    "eso no es lo que te pedi",
    "no me entendiste",
    "mal hecho",
)


MEJORA = (
    "quiero que puedas",
    "quiero que sepas",
    "quiero que aprendas a",
    "coloca en tu codigo",
    "pon en tu codigo",
    "agrega a tu codigo",
    "anade a tu codigo",
    "programa en tu codigo",
    "modifica tu codigo",
    "cambia tu codigo",
    "mejora tu codigo",
    "aprende a",
    "deberias poder",
    "necesito que puedas",
)

ABRIR_PC = re.compile(
    r"^(?:abre|abrir|abreme|lanza|inicia|ejecuta)\s+(?:el programa\s+|la aplicacion\s+|la app\s+|el\s+|la\s+)?(?P<que>.+?)(?:\s+en (?:el|este|mi) (?:pc|computador|computadora|equipo|ordenador))?$"
)

_ultima_orden_vista = ""


def _mejora(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    """«Quiero que puedas abrir Word», «coloca en tu código que…»: una capacidad
    nueva. Se apunta como mejora; la programa solo con el «adelante»."""
    if not limpia.startswith(MEJORA):
        return None

    from ai_architect import autoreparacion
    from ai_architect.commands import conversar

    orden, _dicho = conversar.ultimo_intercambio()
    averia = autoreparacion.registrar(
        "mejora", orden or limpia, "capacidad pedida por el usuario"
    )

    return {
        "respuesta": (
            f"Apuntado como mejora: «{(orden or limpia)[:90]}». Si dices «adelante», la "
            "programo en mi código, corro mis pruebas y te aviso; sin tu orden no toco nada."
        ),
        "averia": averia["id"],
    }


def _calculo(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    """«¿Cuánto es 25 por 4?», «suma 3 y 5», «el 15 por ciento de 200»: sin modelo."""
    from ai_architect.commands import calcular

    salida = calcular.calcular(limpia)

    return {"respuesta": salida["respuesta"]} if salida else None


def _abrir(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    """«Abre Word», «abre Chrome», «abre el escritorio»: programas del PC, sin modelo."""
    m = ABRIR_PC.match(limpia)

    if m is None:
        return None

    que = m["que"].strip()

    # Lo que no es un programa: archivos del proyecto y el celular van por otro lado.
    if que.startswith(("el archivo", "archivo", "la carpeta del proyecto")) or any(
        c in limpia for c in ("celular", "telefono", "movil")
    ):
        return None

    if que in ("la ventana", "ventana", "el panel"):
        return None

    from ai_architect.commands import abrir

    salida = abrir.abrir(que)

    return {"respuesta": salida["explicacion"]}


# Cualquier forma de mandarlo cerrar: «Cerrar», «No, cierra», «apágate ya»,
# «termina el proyecto», «detente». Lo único que no es cerrar es la ventana
# flotante, y esa va antes.
CERRAR_PATRON = re.compile(
    r"^(?:no,?\s+|ya,?\s+|por favor,?\s+)?"
    r"(?:cierra|cerrar|cierrate|apaga|apagar|apagate|termina|terminar|terminate|"
    r"deten|detente|detener|finaliza|finalizar|para|parate|sal|salir|salte|despidete)"
    r"(?:\s+(?:ya|architect|arquitecto|el programa|la sesion|todo|tu ejecucion|"
    r"la ejecucion|el proyecto|la conversacion|architect ya|y cierra|por favor))*$"
)


def _cerrar(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    """«Cierra Architect» se cumple: se despide y se apaga. En la prueba real
    contestaba «aquí sigo» y se quedaba."""
    if limpia not in CERRARSE and CERRAR_PATRON.match(limpia) is None:
        return None

    return {"respuesta": f"Hasta luego, {perfil.como_llamarte()}.", "cerrar": True}


REPOSO_PATRON = re.compile(
    r"^(?:architect,?\s+|arquitecto,?\s+)?"
    r"(?:hiberna|hibernar|hibernate|descansa|descansar|reposa|reposar|duerme|dormir|duermete|"
    r"quedate en reposo|ponte en reposo|entra en reposo|modo reposo|ponte a dormir|ve a dormir|"
    r"a dormir|vuelve a la nebulosa|hazte nebulosa|transformate en nebulosa|conviertete en nebulosa|"
    r"deshazte|relajate)"
    r"(?:\s+(?:un rato|ya|hasta que te llame|hasta que te hable|por ahora|architect|arquitecto))*$"
)


def _reposo(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    """«Descansa», «hiberna», «quédate en reposo»: nebulosa hasta que le hablen."""
    if limpia not in REPOSO and REPOSO_PATRON.match(limpia) is None:
        return None

    return {"respuesta": "Descanso. Llámame cuando quieras.", "rostro": "reposo"}


def _queja(limpia: str, _: datetime | None) -> dict[str, Any] | None:
    """Cuando el usuario dice que lo hizo mal, se apunta como avería con la
    última orden y la última respuesta, y queda a la espera del «adelante»."""
    if limpia not in QUEJA:
        return None

    from ai_architect import autoreparacion
    from ai_architect.commands import conversar

    orden, dicho = conversar.ultimo_intercambio()

    if not orden:
        return {"respuesta": "Dime qué hice mal y lo apunto."}

    autoreparacion.registrar(
        "conversacion",
        orden,
        f"el usuario dice que la respuesta fue incorrecta. Respondí: {dicho[:300]}",
    )

    return {
        "respuesta": (
            f"Apuntado: a «{orden[:80]}» contesté mal. Si dices «adelante», reviso "
            "por qué y lo corrijo; sin tu orden no lo toco."
        )
    }


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
