"""
=========================================================
Encargo

Preguntar lo que falta, en vez de adivinarlo.
=========================================================

"Analicemos un repositorio" no dice cuál. Hasta ahora el arquitecto lo
resolvía por su cuenta: ``project`` vale ``"."`` por defecto, así que
analizaba el repositorio en el que estuviera y no decía nada. Cuando eso
acierta parece listo; cuando falla, ha trabajado media hora sobre el
proyecto equivocado y nadie se entera hasta el final.

Esto añade un paso antes de ejecutar: **decir lo que ha entendido y pedir
lo que falta**.

    tú     Evaluemos un repositorio.
    él     Entendido: revisar un repositorio y puntuarlo. Estoy listo.
           ¿Dónde está? Dime la carpeta.
    tú     autosgsst
    él     [lo hace]

**La regla es estrecha a propósito.** Solo pregunta cuando de verdad le
falta un dato, no cada vez. "Analiza la carpeta autosgsst" ya lo dice todo
y se ejecuta directamente; confirmar ahí sería un paso de más en cada
orden, y eso cansa a la tercera. La diferencia entre preguntar poco y
preguntar siempre es la diferencia entre parecer atento y parecer torpe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.core.texto import contiene, sin_adornos

# Comandos que trabajan **sobre** un repositorio. Sin saber cuál, lo que
# hagan no vale nada.
NECESITAN_SITIO = {
    "review": "revisar el código y puntuarlo",
    "agents": "pasarle los agentes en busca de problemas",
    "analyze": "analizar la estructura",
    "improve": "proponer una mejora del código",
    "auto": "encadenar varias mejoras",
    "changelog": "armar el changelog desde el historial",
}

# Palabras que anuncian una tarea grande sin decir sobre qué. Son las que
# usó el usuario al pedir esto, y las que se usan al empezar algo.
EN_PLURAL = (
    "evaluemos",
    "analicemos",
    "revisemos",
    "construyamos",
    "miremos",
    "trabajemos",
    "empecemos",
    "vamos a evaluar",
    "vamos a revisar",
    "vamos a analizar",
    "quiero evaluar",
    "quiero revisar",
    "quiero analizar",
    "necesito revisar",
)

# Lo que se dice cuando se habla de un sitio sin nombrarlo. Lo indefinido
# («un repositorio») siempre pregunta; lo definido («el proyecto») solo si la
# conversación no está ya dentro de uno: estando en él, «el proyecto» es este.
SIN_NOMBRE = (
    "un repositorio",
    "un proyecto",
    "un programa",
    "una carpeta",
    "un codigo",
)

DEFINIDOS = ("el repositorio", "el proyecto", "el codigo")

# Con qué se reconoce que una carpeta es un proyecto de verdad.
SENAS_DE_PROYECTO = (
    ".git",
    "pyproject.toml",
    "package.json",
    "setup.py",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
)


def es_un_proyecto(base: Path | str) -> bool:
    raiz = Path(base)

    return any((raiz / sena).exists() for sena in SENAS_DE_PROYECTO)


# Lo pedido y todavía sin sitio. Se guarda entero para poder ejecutarlo tal
# cual en cuanto se sepa dónde.
_esperando: dict[str, Any] = {}


def hay_encargo() -> bool:
    return bool(_esperando)


def olvidar() -> None:
    _esperando.clear()


def falta_el_sitio(
    frase: str, nombre: str, carpeta_dicha: str, base: Path | str = "."
) -> bool:
    """Si esa orden necesita un sitio y no lo trae.

    Tres condiciones, y las tres tienen que darse:

    1. El comando trabaja sobre un repositorio.
    2. No se nombró ninguna carpeta — ni el modelo la sacó, ni la frase la
       lleva.
    3. La frase habla del sitio **sin nombrarlo**: "un repositorio", "el
       proyecto". Si dice "revisa" a secas estando dentro de uno, se
       entiende que habla de ese, y preguntarlo sería tonto.
    """
    if nombre not in NECESITAN_SITIO:
        return False

    if carpeta_dicha.strip():
        return False

    limpia = sin_adornos(frase)

    if contiene(limpia, *SIN_NOMBRE) or contiene(limpia, *EN_PLURAL):
        return True

    # «Revisa el proyecto» estando dentro de uno habla de este. Preguntar
    # «¿dónde está?» ahí fue lo primero que cansó en la prueba real.
    if contiene(limpia, *DEFINIDOS):
        return not es_un_proyecto(base)

    return False


def anotar(nombre: str, frase: str, intencion: dict[str, Any]) -> dict[str, Any]:
    """Guarda lo pedido y devuelve lo que hay que contestar."""
    _esperando.clear()
    _esperando.update({"comando": nombre, "frase": frase, "intencion": dict(intencion)})

    return {
        "success": True,
        "executed": False,
        "awaiting": "sitio",
        "command": nombre,
        "explanation": (
            f"Entendido: {NECESITAN_SITIO[nombre]}. Estoy listo.\n\n"
            "¿Dónde está? Dime el nombre de la carpeta y voy."
        ),
    }


def con_el_sitio(frase: str, base: Path | str = ".") -> dict[str, Any] | None:
    """Interpreta la respuesta a "¿dónde está?" y devuelve el encargo listo.

    Devuelve ``None`` si lo dicho no parece una ubicación: entonces no era
    la respuesta a la pregunta sino otra cosa, y sigue su camino normal.
    """
    if not _esperando:
        return None

    dicho = _limpiar(frase)

    if not dicho:
        return None

    # Una frase larga no es el nombre de una carpeta: es otra orden. Se
    # suelta la pregunta y la frase sigue su camino. Sin esto, «examina el
    # archivo X y dime qué hace» se contestaba con «no encuentro ninguna
    # carpeta que se llame examina el archivo…».
    if len(dicho.split()) > 4:
        olvidar()

        return None

    if contiene(dicho, "dejalo", "olvidalo", "da igual", "cancela", "nada"):
        olvidar()

        return {"success": True, "cancelado": True, "explanation": "Nada, lo dejo."}

    from ai_architect.core import rutas

    elegida, parecidas = rutas.resolver(dicho, base)

    if elegida is None:
        if not parecidas:
            # Ni carpeta ni parecidas: probablemente no estaba
            # contestando a la pregunta.
            return None

        return {
            "success": True,
            "awaiting": "sitio",
            "explanation": (
                f"No encuentro ninguna que se llame {dicho}. "
                f"Tengo estas cerca: {rutas.nombrar(parecidas)}."
            ),
        }

    pedido = dict(_esperando)

    olvidar()

    return {
        "success": True,
        "listo": True,
        "comando": pedido["comando"],
        "frase": pedido["frase"],
        # La carpeta que acaba de decir manda sobre el `project` que puso el
        # modelo. Sin esto pasaba lo que este modulo venia a evitar: se
        # resolvia "autosgsst" correctamente y se analizaba otra cosa,
        # porque el modelo habia puesto `project: "."` y ese "." ganaba.
        "intencion": {**pedido["intencion"], "project": str(elegida)},
        "sitio": elegida,
    }


def _limpiar(frase: str) -> str:
    """La frase sin lo que la envuelve: queda el nombre de la carpeta.

    Se dice "en la carpeta autosgsst" o "está en autosgsst", y buscar eso
    tal cual no encuentra nada.
    """
    limpia = sin_adornos(frase)

    for sobra in (
        "esta en ",
        "estan en ",
        "en la carpeta ",
        "la carpeta ",
        "en el proyecto ",
        "el proyecto ",
        "en la ruta ",
        "en ",
        "es ",
    ):
        if limpia.startswith(sobra):
            limpia = limpia[len(sobra) :]

    return limpia.strip()
