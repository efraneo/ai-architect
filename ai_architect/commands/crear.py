"""
=========================================================
Crear

Documentos, tablas y gráficas, y decidir dónde van.
=========================================================

Hasta aquí el arquitecto contestaba. Esto le deja **producir**: un resumen,
una tabla, una gráfica, un trabajo de clase. Lo que sale es un archivo que
se puede abrir, imprimir o entregar.

**Por qué HTML y no Word.** Un `.docx` necesita una librería aparte y luego
un Word que lo abra. Un HTML se abre en cualquier navegador, se imprime a
PDF desde ahí, y se puede mirar el archivo con un editor de texto si algo
sale mal. Las tablas se guardan además en `.csv`, que es lo que se abre en
Excel sin discusión.

**Por qué no matplotlib.** Una gráfica de barras o de líneas es geometría:
se dibuja en SVG con veinte líneas y sale nítida a cualquier tamaño, sin
arrastrar una dependencia de las grandes ni una fuente que puede no estar.

**Por qué el contenido viene estructurado.** Se le pide al modelo secciones
y datos, no HTML. Un modelo escribiendo etiquetas a mano acaba antes o
después con un `<div>` sin cerrar, y entonces el documento no se ve y no
hay forma de saber por qué. Si vienen los datos, el HTML lo montamos aquí
y siempre está bien formado.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_architect.core import perfil
from ai_architect.core.texto import contiene, sin_adornos

INSTRUCCIONES = """Eres el arquitecto, y {trato} te ha pedido que le
prepares algo. Tu trabajo es redactarlo entero y bien, como un experto en
el tema, sea el que sea.

Devuelve SOLO un objeto JSON, sin markdown y sin explicación, con una de
estas formas:

DOCUMENTO (informe, resumen, trabajo, apuntes, respuesta larga)
{{"tipo": "documento",
  "titulo": "...",
  "resumen": "una o dos frases, para decirlas en voz alta",
  "secciones": [{{"titulo": "...", "parrafos": ["...", "..."]}}]}}

TABLA (comparativas, listados, datos)
{{"tipo": "tabla",
  "titulo": "...",
  "resumen": "...",
  "columnas": ["...", "..."],
  "filas": [["...", "..."], ["...", "..."]]}}

GRAFICA (evolución, comparación de cantidades)
{{"tipo": "grafica",
  "titulo": "...",
  "resumen": "...",
  "forma": "barras" o "lineas",
  "eje": "qué mide",
  "etiquetas": ["ene", "feb"],
  "valores": [10, 20]}}

REGLAS
- Escribe en español, con la profundidad de quien sabe del tema. Si es un
  trabajo de clase, que esté completo: nada de esquemas ni de "aquí irían
  los datos".
- `resumen` es lo único que se va a leer en voz alta. Una o dos frases,
  sin listas ni símbolos.
- En una tabla, todas las filas con tantas celdas como columnas.
- En una gráfica, tantos valores como etiquetas, y los valores números.
- Si te piden varias cosas a la vez, elige la que mejor lo resuelva.

FECHA DE HOY
{momento}

LO QUE TE HA PEDIDO
{peticion}
"""


# Dónde se puede guardar sin abrir un diálogo. Los nombres son los que se
# dicen hablando, no los del disco.
def escritorio() -> Path:
    """La carpeta del escritorio, esté donde esté.

    En un Windows en español con OneDrive activo, ``~/Desktop`` **no
    existe**: el escritorio está en ``~/OneDrive/Escritorio``. Dar por
    hecho lo primero es guardar el documento en una carpeta recién creada
    que el usuario no va a mirar nunca.
    """
    candidatas = [
        Path.home() / "OneDrive" / "Escritorio",
        Path.home() / "OneDrive" / "Desktop",
        Path.home() / "Escritorio",
        Path.home() / "Desktop",
    ]

    for carpeta in candidatas:
        if carpeta.is_dir():
            return carpeta

    return Path.home()


def documentos() -> Path:
    for carpeta in (
        Path.home() / "Documents",
        Path.home() / "Documentos",
        Path.home() / "OneDrive" / "Documentos",
    ):
        if carpeta.is_dir():
            return carpeta

    return escritorio()


# Lo generado y todavía sin guardar. Se pregunta dónde va, y la respuesta
# llega en la frase siguiente.
_pendiente: dict[str, Any] = {}


def hay_pendiente() -> bool:
    return bool(_pendiente)


def olvidar() -> None:
    _pendiente.clear()


# --- Generar -----------------------------------------------------------------


def run(peticion: str, engine: Any = None) -> dict[str, Any]:
    """Prepara el documento y pregunta dónde guardarlo."""
    if not peticion.strip():
        return {"success": False, "error": "no dijiste qué quieres que prepare"}

    try:
        crudo = _pedir(engine, peticion)

    except Exception as e:  # noqa: BLE001 - un proveedor caído no revienta
        return {"success": False, "error": f"el proveedor falló: {e}"}

    datos = _leer_json(crudo)

    if datos is None:
        return {"success": False, "error": "no pude armar el documento"}

    try:
        contenido, extension = _componer(datos)

    except (KeyError, TypeError, ValueError) as e:
        return {"success": False, "error": f"el documento vino mal formado: {e}"}

    _pendiente.clear()
    _pendiente.update(
        {
            "titulo": str(datos.get("titulo") or "documento"),
            "nombre": _nombre_de_archivo(str(datos.get("titulo") or "documento")),
            "extension": extension,
            "contenido": contenido,
            "datos": datos,
        }
    )

    resumen = str(datos.get("resumen") or "").strip()

    return {
        "success": True,
        "executed": True,
        "awaiting": "destino",
        "title": _pendiente["titulo"],
        "kind": datos.get("tipo"),
        "explanation": (
            f"{resumen} Ya lo tengo listo. "
            "¿Dónde lo guardo? En el escritorio, en documentos, "
            "o dímelo y lo eliges tú."
        ),
        "panel": {
            "tipo": "texto",
            "titulo": _pendiente["titulo"],
            "cuerpo": _vista_previa(datos),
        },
    }


def _pedir(engine: Any, peticion: str) -> str:
    proveedor = engine

    if proveedor is None:
        from ai_architect.providers.provider_manager import ProviderManager

        proveedor = ProviderManager()

    from ai_architect.commands.pide import _momento

    return str(
        proveedor.generate(
            INSTRUCCIONES.format(
                trato=perfil.como_llamarte(),
                momento=_momento(),
                peticion=peticion,
            )
        )
    )


def _leer_json(texto: str) -> dict[str, Any] | None:
    if not texto:
        return None

    for intento in (texto, ""):
        if not intento:
            hallado = re.search(r"\{.*\}", texto, re.DOTALL)

            if hallado is None:
                return None

            intento = hallado.group(0)

        try:
            leido = json.loads(intento)

        except (ValueError, TypeError):
            continue

        if isinstance(leido, dict):
            return leido

    return None


# --- Guardar -----------------------------------------------------------------

# Los sitios que se pueden decir hablando. Se guardan los **nombres**, no
# las funciones: un diccionario de funciones las ata en el import, y
# entonces la carpeta queda congelada desde el arranque —da igual que el
# usuario mueva el escritorio o que una prueba quiera otro sitio—.
DESTINOS = ("escritorio", "documentos")


def carpeta_de(nombre: str) -> Path:
    """La carpeta que toca, resuelta ahora y no al importar."""
    return documentos() if nombre == "documentos" else escritorio()


ELEGIR = (
    "lo elijo yo",
    "elijo yo",
    "yo elijo",
    "quiero elegir",
    "dejame elegir",
    "abre el explorador",
    "explorador",
    "otra carpeta",
    "en otro sitio",
    "yo la escojo",
    "escojo yo",
    "preguntame",
)

CANCELAR = ("no lo guardes", "dejalo", "olvidalo", "cancela", "no hace falta")


def donde_guardarlo(frase: str) -> dict[str, Any] | None:
    """Interpreta la respuesta a "¿dónde lo guardo?". Sin modelo.

    Es una respuesta de dos palabras a una pregunta que se acaba de hacer:
    mandarla a un modelo son dos segundos para elegir entre tres opciones
    que ya se conocen.
    """
    if not _pendiente:
        return None

    limpia = sin_adornos(frase)

    if not limpia:
        return None

    if contiene(limpia, *CANCELAR):
        olvidar()

        return {"success": True, "explanation": "Nada, lo dejo estar."}

    if contiene(limpia, *ELEGIR):
        return guardar_donde_diga()

    for nombre in DESTINOS:
        if nombre in limpia:
            return guardar_en(carpeta_de(nombre))

    # Puede haber dicho una carpeta suya: "guárdalo en autosgsst".
    from ai_architect.core import rutas

    dicho = re.sub(r"^(guardalo|guardala|ponlo|ponla|en|el|la|al)\s+", "", limpia)

    elegida, _ = rutas.resolver(dicho, Path.cwd())

    if elegida is not None:
        return guardar_en(elegida)

    return None


def guardar_en(carpeta: Path) -> dict[str, Any]:
    """Escribe lo pendiente en esa carpeta y lo abre."""
    if not _pendiente:
        return {"success": False, "error": "no tengo nada preparado"}

    destino = _sin_pisar(carpeta / (_pendiente["nombre"] + _pendiente["extension"]))

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)

        # Un `.docx` es binario y el HTML es texto. Escribir bytes con
        # `write_text` revienta; escribir el ZIP como texto da un archivo
        # que Word abre y muestra vacío, que es peor porque parece que
        # funcionó.
        if _pendiente.get("binario") is not None:
            destino.write_bytes(_pendiente["binario"])

        else:
            destino.write_text(_pendiente["contenido"], encoding="utf-8")

    except OSError as e:
        return {"success": False, "error": f"no pude guardarlo: {e}"}

    extras = _extras(destino)

    titulo = _pendiente["titulo"]

    olvidar()

    _abrir(destino)

    dicho = f"Guardado en {carpeta.name or carpeta}. Te lo abro."

    return {
        "success": True,
        "executed": True,
        "path": str(destino),
        "extras": [str(e) for e in extras],
        "explanation": dicho,
        "panel": {
            "tipo": "archivo",
            "titulo": titulo,
            "ruta": str(destino),
            "carpeta": str(carpeta),
        },
    }


def guardar_donde_diga() -> dict[str, Any]:
    """Abre el explorador de Windows para que elija la ruta."""
    if not _pendiente:
        return {"success": False, "error": "no tengo nada preparado"}

    elegido = _dialogo(_pendiente["nombre"] + _pendiente["extension"])

    if not elegido:
        return {
            "success": True,
            "explanation": "No elegiste ninguna carpeta. Lo dejo preparado.",
        }

    # Con la ruta exacta que eligió, no solo su carpeta: si se molestó en
    # escribir un nombre en el diálogo, es el que quiere.
    return _guardar_exacto(Path(elegido))


def _guardar_exacto(destino: Path) -> dict[str, Any]:
    """Guarda con el nombre y la ruta que eligió, sin retocarlos."""
    titulo = _pendiente["titulo"]

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)

        # Un `.docx` es binario y el HTML es texto. Escribir bytes con
        # `write_text` revienta; escribir el ZIP como texto da un archivo
        # que Word abre y muestra vacío, que es peor porque parece que
        # funcionó.
        if _pendiente.get("binario") is not None:
            destino.write_bytes(_pendiente["binario"])

        else:
            destino.write_text(_pendiente["contenido"], encoding="utf-8")

    except OSError as e:
        return {"success": False, "error": f"no pude guardarlo: {e}"}

    extras = _extras(destino)

    olvidar()

    _abrir(destino)

    return {
        "success": True,
        "executed": True,
        "path": str(destino),
        "extras": [str(e) for e in extras],
        "explanation": f"Guardado donde dijiste, en {destino.parent.name}. Te lo abro.",
        "panel": {
            "tipo": "archivo",
            "titulo": titulo,
            "ruta": str(destino),
            "carpeta": str(destino.parent),
        },
    }


def _dialogo(sugerido: str) -> str:
    """El explorador de archivos de Windows. Bloquea hasta que elige.

    `tkinter` viene con Python, así que esto no añade dependencias. La
    ventana se crea y se destruye aquí: dejarla viva se queda de fondo y
    la segunda vez ya no aparece delante.
    """
    try:
        import tkinter
        from tkinter import filedialog

    except ImportError:
        return ""

    try:
        raiz = tkinter.Tk()
        raiz.withdraw()
        raiz.attributes("-topmost", True)

        elegido = filedialog.asksaveasfilename(
            parent=raiz,
            title="¿Dónde lo guardo?",
            initialfile=sugerido,
            initialdir=str(escritorio()),
            defaultextension=Path(sugerido).suffix,
        )

        raiz.destroy()

    except Exception:  # noqa: BLE001 - sin ventanas se sigue sin diálogo
        return ""

    return str(elegido or "")


def _extras(destino: Path) -> list[Path]:
    """Lo que acompaña al documento. Una tabla va también en CSV.

    El HTML se mira; el CSV se abre en Excel. Pedir que se elija entre los
    dos cuando cuesta un archivo más es hacer trabajar al usuario de balde.
    """
    datos = _pendiente.get("datos") or {}

    if datos.get("tipo") != "tabla":
        return []

    hoja = destino.with_suffix(".csv")

    try:
        with hoja.open("w", encoding="utf-8-sig", newline="") as archivo:
            escritor = csv.writer(archivo, delimiter=";")
            escritor.writerow(datos.get("columnas") or [])
            escritor.writerows(datos.get("filas") or [])

    except OSError:
        return []

    return [hoja]


def _abrir(destino: Path) -> None:
    try:
        webbrowser.open(destino.as_uri())

    except (OSError, ValueError):
        pass


def _sin_pisar(destino: Path) -> Path:
    """Nunca sobrescribe. Un documento perdido no se recupera."""
    if not destino.exists():
        return destino

    for numero in range(2, 100):
        intento = destino.with_name(f"{destino.stem} ({numero}){destino.suffix}")

        if not intento.exists():
            return intento

    return destino.with_name(f"{destino.stem} {os.getpid()}{destino.suffix}")


def _nombre_de_archivo(titulo: str) -> str:
    limpio = re.sub(r"[^\w\s-]", "", titulo, flags=re.UNICODE).strip()

    return (re.sub(r"\s+", " ", limpio) or "documento")[:70]


# --- Montar el archivo -------------------------------------------------------


def _componer(datos: dict[str, Any]) -> tuple[str, str]:
    tipo = str(datos.get("tipo") or "documento")

    cuerpo = {
        "tabla": _tabla,
        "grafica": _grafica,
    }.get(
        tipo, _documento
    )(datos)

    return (_pagina(str(datos.get("titulo") or "Documento"), cuerpo), ".html")


def _escapar(texto: Any) -> str:
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _documento(datos: dict[str, Any]) -> str:
    partes = []

    for seccion in datos.get("secciones") or []:
        if seccion.get("titulo"):
            partes.append(f"<h2>{_escapar(seccion['titulo'])}</h2>")

        for parrafo in seccion.get("parrafos") or []:
            partes.append(f"<p>{_escapar(parrafo)}</p>")

    return "\n".join(partes) or "<p>Sin contenido.</p>"


def _tabla(datos: dict[str, Any]) -> str:
    columnas = datos.get("columnas") or []
    filas = datos.get("filas") or []

    cabecera = "".join(f"<th>{_escapar(c)}</th>" for c in columnas)

    cuerpo = "".join(
        "<tr>" + "".join(f"<td>{_escapar(celda)}</td>" for celda in fila) + "</tr>"
        for fila in filas
    )

    return f"<table><thead><tr>{cabecera}</tr></thead><tbody>{cuerpo}</tbody></table>"


ANCHO = 760
ALTO = 380
MARGEN = 56


def _grafica(datos: dict[str, Any]) -> str:
    """La gráfica, en SVG dibujado aquí.

    Sin matplotlib: unas barras o una línea son geometría, y así sale
    nítida a cualquier tamaño y sin una dependencia de trescientos megas.
    """
    etiquetas = [str(e) for e in (datos.get("etiquetas") or [])]
    valores = [float(v) for v in (datos.get("valores") or [])]

    if not valores or len(valores) != len(etiquetas):
        raise ValueError("la gráfica necesita tantos valores como etiquetas")

    alto_util = ALTO - MARGEN * 2
    ancho_util = ANCHO - MARGEN * 2

    tope = max(valores + [0]) or 1
    suelo = min(valores + [0])
    rango = (tope - suelo) or 1

    def y_de(valor: float) -> float:
        return MARGEN + alto_util - (valor - suelo) / rango * alto_util

    piezas = [
        f'<line x1="{MARGEN}" y1="{MARGEN + alto_util}" '
        f'x2="{MARGEN + ancho_util}" y2="{MARGEN + alto_util}" class="eje"/>'
    ]

    paso = ancho_util / max(len(valores), 1)

    if str(datos.get("forma") or "barras") == "lineas":
        puntos = " ".join(
            f"{MARGEN + paso * (i + 0.5):.1f},{y_de(v):.1f}"
            for i, v in enumerate(valores)
        )

        piezas.append(f'<polyline points="{puntos}" class="linea"/>')

        piezas.extend(
            f'<circle cx="{MARGEN + paso * (i + 0.5):.1f}" cy="{y_de(v):.1f}" r="4"/>'
            for i, v in enumerate(valores)
        )

    else:
        ancho_barra = paso * 0.62

        for i, valor in enumerate(valores):
            x = MARGEN + paso * i + (paso - ancho_barra) / 2
            y = y_de(valor)

            piezas.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{ancho_barra:.1f}" '
                f'height="{MARGEN + alto_util - y:.1f}" rx="4" class="barra"/>'
            )

    for i, (etiqueta, valor) in enumerate(zip(etiquetas, valores, strict=False)):
        centro = MARGEN + paso * (i + 0.5)

        piezas.append(
            f'<text x="{centro:.1f}" y="{ALTO - MARGEN + 22}" '
            f'class="etiqueta">{_escapar(etiqueta)}</text>'
        )

        piezas.append(
            f'<text x="{centro:.1f}" y="{y_de(valor) - 10:.1f}" '
            f'class="cifra">{_escapar(_numero(valor))}</text>'
        )

    eje = datos.get("eje")

    titulo_eje = (
        f'<text x="{MARGEN}" y="{MARGEN - 22}" class="eje-nombre">{_escapar(eje)}</text>'
        if eje
        else ""
    )

    return (
        f'<svg viewBox="0 0 {ANCHO} {ALTO}" class="grafica" '
        f'xmlns="http://www.w3.org/2000/svg">{titulo_eje}' + "".join(piezas) + "</svg>"
    )


def _numero(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".") if valor >= 100 else f"{valor:g}"


def _vista_previa(datos: dict[str, Any]) -> str:
    """Lo justo para reconocerlo en la ventana flotante."""
    if datos.get("tipo") == "tabla":
        columnas = ", ".join(str(c) for c in (datos.get("columnas") or []))

        return f"{len(datos.get('filas') or [])} filas\n{columnas}"

    if datos.get("tipo") == "grafica":
        return f"{len(datos.get('valores') or [])} datos\n{datos.get('eje') or ''}"

    trozos = io.StringIO()

    for seccion in (datos.get("secciones") or [])[:3]:
        trozos.write(str(seccion.get("titulo") or "") + "\n")

        for parrafo in (seccion.get("parrafos") or [])[:1]:
            trozos.write(str(parrafo)[:260] + "\n\n")

    return trozos.getvalue().strip() or str(datos.get("resumen") or "")


PLANTILLA = """<meta charset="utf-8">
<title>{titulo}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{
    margin: 0; padding: 56px 24px 96px;
    background: #f4f5f8; color: #17181d;
    font: 16px/1.75 Georgia, "Times New Roman", serif;
  }}
  main {{
    max-width: 780px; margin: 0 auto; padding: 60px 64px 72px;
    background: #fff; border-radius: 4px;
    box-shadow: 0 2px 28px rgba(20, 24, 50, .09);
  }}
  h1 {{
    margin: 0 0 6px; font-size: 30px; line-height: 1.25;
    font-weight: 600; letter-spacing: -.01em;
  }}
  .firma {{
    margin: 0 0 40px; padding-bottom: 22px;
    border-bottom: 1px solid #e3e5ec;
    font: 13px/1.6 system-ui, sans-serif; color: #6b7080;
  }}
  h2 {{
    margin: 38px 0 12px; font-size: 20px; font-weight: 600;
    letter-spacing: -.005em;
  }}
  p {{ margin: 0 0 16px; }}
  table {{
    width: 100%; margin: 26px 0; border-collapse: collapse;
    font: 14px/1.6 system-ui, sans-serif;
  }}
  th, td {{ padding: 11px 14px; text-align: left; border-bottom: 1px solid #e6e8ef; }}
  th {{
    background: #f7f8fb; font-weight: 600; font-size: 12px;
    letter-spacing: .06em; text-transform: uppercase; color: #545a6b;
  }}
  tbody tr:hover {{ background: #fafbfd; }}
  .grafica {{ width: 100%; height: auto; margin: 30px 0; }}
  .grafica .eje {{ stroke: #c9cdd8; stroke-width: 1; }}
  .grafica .barra {{ fill: #3c5fd0; }}
  .grafica .linea {{ fill: none; stroke: #3c5fd0; stroke-width: 2.5; }}
  .grafica circle {{ fill: #3c5fd0; }}
  .grafica .etiqueta {{
    fill: #6b7080; font: 12px system-ui, sans-serif; text-anchor: middle;
  }}
  .grafica .cifra {{
    fill: #2b3040; font: 600 12px system-ui, sans-serif; text-anchor: middle;
  }}
  .grafica .eje-nombre {{ fill: #6b7080; font: 12px system-ui, sans-serif; }}
  @media print {{
    body {{ padding: 0; background: #fff; }}
    main {{ box-shadow: none; padding: 0; max-width: none; }}
  }}
</style>

<main>
  <h1>{titulo}</h1>
  <p class="firma">{firma}</p>
  {cuerpo}
</main>
"""


def _pagina(titulo: str, cuerpo: str) -> str:
    from ai_architect.commands.pide import DIAS, MESES

    hoy = datetime.now()

    fecha = f"{DIAS[hoy.weekday()]} {hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"

    return PLANTILLA.format(
        titulo=_escapar(titulo),
        firma=f"{_escapar(perfil.como_llamarte())} · {fecha}",
        cuerpo=cuerpo,
    )


# =========================================================
# Word
#
# "Pasalo a Word" era la peticion mas razonable del mundo y no habia forma
# de hacerlo: lo que salia en la ventana flotante se quedaba ahi.
#
# Un `.docx` no necesita ninguna libreria: **es un ZIP con tres XML
# dentro**. Word lo abre sin rechistar y sin modo de compatibilidad. La
# alternativa —guardar HTML con extension `.doc`— tambien abre, pero Word
# avisa de que el formato no coincide y queda como un apano.
# =========================================================

TIPOS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

RELACIONES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOCUMENTO_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>{cuerpo}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>
<w:pgMar w:top="1418" w:right="1418" w:bottom="1418" w:left="1418"/>
</w:sectPr></w:body></w:document>"""


def _parrafo_word(texto: str, estilo: str = "") -> str:
    """Un parrafo de Word. `estilo` marca los titulos.

    El tamano va a mano en vez de con estilos con nombre: los estilos viven
    en `styles.xml`, que es una cuarta pieza del paquete, y para tres
    tamanos de letra no compensa arrastrarla.
    """
    tamanos = {"h1": "36", "h2": "28"}

    if estilo in tamanos:
        medida = tamanos[estilo]

        formato = (
            f'<w:rPr><w:b w:val="1"/><w:sz w:val="{medida}"/>'
            f'<w:szCs w:val="{medida}"/></w:rPr>'
        )
        espacio = '<w:pPr><w:spacing w:before="280" w:after="120"/></w:pPr>'

    else:
        formato = '<w:rPr><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
        espacio = (
            '<w:pPr><w:spacing w:after="160" w:line="276" w:lineRule="auto"/></w:pPr>'
        )

    return (
        f"<w:p>{espacio}<w:r>{formato}"
        f'<w:t xml:space="preserve">{_escapar(texto)}</w:t></w:r></w:p>'
    )


def word(titulo: str, bloques: list[tuple[str, str]]) -> bytes:
    """El `.docx` entero, en memoria. `bloques` son pares (estilo, texto)."""
    import zipfile

    cuerpo = _parrafo_word(titulo, "h1") + "".join(
        _parrafo_word(texto, estilo) for estilo, texto in bloques
    )

    memoria = io.BytesIO()

    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as paquete:
        paquete.writestr("[Content_Types].xml", TIPOS)
        paquete.writestr("_rels/.rels", RELACIONES)
        paquete.writestr("word/document.xml", DOCUMENTO_XML.format(cuerpo=cuerpo))

    return memoria.getvalue()


# Lo ultimo que contesto, por si se pide pasarlo a un archivo.
_ultimo: dict[str, Any] = {}


def recordar(titulo: str, texto: str) -> None:
    """Guarda la ultima respuesta, para poder convertirla despues."""
    if not (texto or "").strip():
        return

    _ultimo.clear()
    _ultimo.update({"titulo": titulo or "Respuesta", "texto": texto})


A_WORD = (
    "pasalo a word",
    "pasala a word",
    "pasame eso a word",
    "en word",
    "a word",
    "documento de word",
    "archivo de word",
    "conviertelo a word",
    "guardalo en word",
)


def pedir_word(frase: str) -> dict[str, Any] | None:
    """Si pide pasar a Word lo ultimo, lo prepara y pregunta donde va."""
    if not contiene(frase, *A_WORD):
        return None

    fuente = _de_lo_pendiente() or _de_lo_ultimo()

    if fuente is None:
        return {
            "success": True,
            "explanation": "No tengo nada reciente que pasar a Word.",
        }

    titulo, bloques = fuente

    _pendiente.clear()
    _pendiente.update(
        {
            "titulo": titulo,
            "nombre": _nombre_de_archivo(titulo),
            "extension": ".docx",
            "contenido": None,
            "binario": word(titulo, bloques),
            "datos": {"tipo": "word"},
        }
    )

    return {
        "success": True,
        "awaiting": "destino",
        "explanation": (
            "Listo, en Word. Donde lo guardo? En el escritorio, en "
            "documentos, o dimelo y lo eliges tu."
        ),
        "panel": {"tipo": "texto", "titulo": titulo, "cuerpo": "Documento de Word"},
    }


def _de_lo_pendiente() -> tuple[str, list[tuple[str, str]]] | None:
    """Lo que estaba a punto de guardarse, pero en Word."""
    datos = _pendiente.get("datos") or {}

    if datos.get("tipo") == "tabla":
        filas = [" - ".join(str(c) for c in fila) for fila in datos.get("filas") or []]

        return (
            str(datos.get("titulo") or "Tabla"),
            [("h2", " - ".join(str(c) for c in datos.get("columnas") or []))]
            + [("", f) for f in filas],
        )

    bloques: list[tuple[str, str]] = []

    for seccion in datos.get("secciones") or []:
        if seccion.get("titulo"):
            bloques.append(("h2", str(seccion["titulo"])))

        bloques.extend(("", str(p)) for p in seccion.get("parrafos") or [])

    if not bloques:
        return None

    return (str(datos.get("titulo") or "Documento"), bloques)


def _de_lo_ultimo() -> tuple[str, list[tuple[str, str]]] | None:
    """Lo que se acaba de contestar, tal cual salio en la ventana."""
    if not _ultimo:
        return None

    bloques: list[tuple[str, str]] = []

    for trozo in str(_ultimo["texto"]).split(chr(10)):
        limpio = trozo.strip()

        if not limpio:
            continue

        # Los titulos que pone el experto cuando contestan varios.
        if limpio.startswith("—") and limpio.endswith("—"):
            bloques.append(("h2", limpio.strip("— ").capitalize()))

        else:
            bloques.append(("", limpio))

    return (str(_ultimo["titulo"]), bloques) if bloques else None
