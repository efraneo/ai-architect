"""
=========================================================
Word

Escribir en Microsoft Word como si alguien tecleara: dictado, párrafos, tablas.
=========================================================

Va por COM (``pywin32``): se conecta al Word abierto, o lo abre, y escribe en
el documento activo con ``Selection.TypeText``. Solo Windows con Office. Si
falta algo, cada función lo dice en vez de reventar.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

# Lo que se dice y lo que se escribe. Se aplican en orden: lo largo antes que
# lo corto («punto y coma» antes que «punto»).
SIGNOS = (
    # Primero lo que abre y cierra; al final «punto» y «coma», que son los más
    # cortos y se comerían a los demás.
    ("abre parentesis", "("),
    ("cierra parentesis", ")"),
    ("abre comillas", "«"),
    ("cierra comillas", "»"),
    ("comillas", '"'),
    ("abre interrogacion", "¿"),
    ("cierra interrogacion", "?"),
    ("signo de interrogacion", "?"),
    ("abre exclamacion", "¡"),
    ("cierra exclamacion", "!"),
    ("signo de exclamacion", "!"),
    ("puntos suspensivos", "... "),
    ("punto y aparte", ".\n"),
    ("punto y a parte", ".\n"),
    ("punto a parte", ".\n"),
    ("punto aparte", ".\n"),
    ("punto y seguido", ". "),
    ("punto seguido", ". "),
    ("punto y coma", "; "),
    ("dos puntos", ": "),
    ("punto final", "."),
    ("nueva linea", "\n"),
    ("salto de linea", "\n"),
    ("nuevo parrafo", "\n"),
    ("otro parrafo", "\n"),
    ("tabulador", "\t"),
    ("guion", "-"),
    ("punto", ". "),
    ("coma", ", "),
)


def _app() -> Any:
    """La aplicación de Word: la abierta, o una nueva. Lanza si no hay COM."""
    import win32com.client  # type: ignore[import-not-found]

    try:
        return win32com.client.GetActiveObject("Word.Application")

    except Exception:  # noqa: BLE001 - no estaba abierto: se abre
        return win32com.client.Dispatch("Word.Application")


def disponible() -> bool:
    try:
        import win32com.client  # type: ignore[import-not-found]  # noqa: F401

    except ImportError:
        return False

    if sys.platform != "win32":
        return False

    try:
        import winreg

        winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "Word.Application")

    except OSError:
        return False

    return True


def abrir() -> dict[str, Any]:
    """Deja Word visible con un documento donde escribir."""
    try:
        app = _app()
        app.Visible = True

        if app.Documents.Count == 0:
            app.Documents.Add()

        app.Activate()

    except Exception as e:  # noqa: BLE001 - se dice
        return {"ok": False, "error": f"No pude abrir Word: {e}"}

    return {"ok": True, "documentos": int(app.Documents.Count)}


def puntuar(texto: str) -> str:
    """Convierte lo dicho («hola coma mundo punto») en texto puntuado."""
    from ai_architect.core.texto import sin_adornos

    salida = texto

    for dicho, signo in SIGNOS:
        # Sin tildes ni mayúsculas para reconocer la orden; se reemplaza en el
        # texto original respetando lo demás.
        # «punto» y «coma» pueden venir con su propio signo pegado por el
        # transcriptor («tres punto.»): se lo tragan. Los demás no tocan lo de al lado.
        cola = r"\b[.,]?\s*" if dicho in ("punto", "coma", "punto final") else r"\b\s*"
        patron = re.compile(
            r"\s*\b" + r"\s+".join(re.escape(p) for p in dicho.split()) + cola,
            re.IGNORECASE,
        )
        salida = _reemplazar_sin_tildes(patron, salida, signo, sin_adornos)

    # Después de un punto o salto va mayúscula; el espacio doble sobra.
    salida = re.sub(r"[ \t]{2,}", " ", salida)
    salida = re.sub(
        r"(^|[.!?]\s+|\n)([a-záéíóúñ])",
        lambda m: m.group(1) + m.group(2).upper(),
        salida,
    )

    return salida.strip(" ")


def _reemplazar_sin_tildes(
    patron: re.Pattern[str], texto: str, signo: str, plano: Any
) -> str:
    """Busca el patrón sobre una copia sin tildes de la misma longitud."""
    import unicodedata

    def sin_tilde(c: str) -> str:
        base = unicodedata.normalize("NFKD", c)[:1] or c

        return base if base.isascii() else c

    copia = "".join(sin_tilde(c) for c in texto)
    partes: list[str] = []
    ultimo = 0

    for m in patron.finditer(copia):
        partes.append(texto[ultimo : m.start()])

        # Un signo pegado a la palabra anterior; un salto, sin espacio antes.
        if signo.endswith("\n") or signo in (")", "»", "?", "!", "...", "... "):
            partes[-1] = partes[-1].rstrip()

        partes.append(signo)
        ultimo = m.end()

    partes.append(texto[ultimo:])

    return "".join(partes)


def escribir(texto: str) -> dict[str, Any]:
    """Escribe en el documento activo, con signos y párrafos."""
    if not texto.strip():
        return {"ok": True, "escrito": ""}

    try:
        app = _app()
        app.Visible = True

        if app.Documents.Count == 0:
            app.Documents.Add()

        seleccion = app.Selection
        puntuado = puntuar(texto)

        for i, trozo in enumerate(puntuado.split("\n")):
            if i:
                seleccion.TypeParagraph()

            if trozo:
                seleccion.TypeText(
                    trozo if trozo.endswith((" ", "(", "¿", "¡", "«")) else trozo + " "
                )

    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"No pude escribir en Word: {e}"}

    return {"ok": True, "escrito": puntuado}


def parrafo() -> dict[str, Any]:
    try:
        _app().Selection.TypeParagraph()

    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}

    return {"ok": True}


def tabla(
    filas: int, columnas: int, encabezados: list[str] | None = None
) -> dict[str, Any]:
    """Inserta una tabla donde está el cursor, con bordes, y opcionalmente encabezados."""
    filas = max(1, min(int(filas), 200))
    columnas = max(1, min(int(columnas), 30))

    try:
        app = _app()
        app.Visible = True

        if app.Documents.Count == 0:
            app.Documents.Add()

        seleccion = app.Selection

        if seleccion.Start != seleccion.Paragraphs(1).Range.Start:
            seleccion.TypeParagraph()

        t = app.ActiveDocument.Tables.Add(seleccion.Range, filas, columnas)
        t.Borders.Enable = True

        for i, titulo in enumerate((encabezados or [])[:columnas]):
            t.Cell(1, i + 1).Range.Text = titulo
            t.Cell(1, i + 1).Range.Font.Bold = True

        # El cursor, después de la tabla, para seguir dictando.
        fin = t.Range
        fin.Collapse(0)
        fin.Select()
        app.Selection.TypeParagraph()

    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"No pude insertar la tabla: {e}"}

    return {"ok": True, "filas": filas, "columnas": columnas}


def celda(fila: int, columna: int, texto: str) -> dict[str, Any]:
    """Escribe en una celda de la última tabla del documento."""
    try:
        app = _app()
        tablas = app.ActiveDocument.Tables

        if tablas.Count == 0:
            return {"ok": False, "error": "No hay ninguna tabla en el documento."}

        tablas(tablas.Count).Cell(int(fila), int(columna)).Range.Text = texto

    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"No pude escribir en la celda: {e}"}

    return {"ok": True}


def deshacer(veces: int = 1) -> dict[str, Any]:
    try:
        _app().ActiveDocument.Undo(int(veces))

    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}

    return {"ok": True}


def guardar(
    nombre: str = "", carpeta: Path | None = None, forzar_nombre: bool = False
) -> dict[str, Any]:
    """Guarda el documento activo (como .docx en el escritorio si es nuevo).
    Sin nombre, se llama «Dictado <fecha y hora>» para no pisar otro."""
    try:
        app = _app()
        doc = app.ActiveDocument

        if doc.Path and not nombre and not forzar_nombre:
            doc.Save()

            return {"ok": True, "ruta": str(Path(doc.Path) / doc.Name)}

        from ai_architect.commands.crear_carpetas import escritorio

        base = carpeta or escritorio()

        if not nombre:
            import time

            nombre = "Dictado " + time.strftime("%Y-%m-%d %H.%M")

        limpio = re.sub(r"[^\w\s.-]", "", nombre).strip() or "Dictado"

        if not limpio.lower().endswith(".docx"):
            limpio += ".docx"

        destino = Path(base) / limpio
        doc.SaveAs2(str(destino))

    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"No pude guardar: {e}"}

    return {"ok": True, "ruta": str(destino)}


def texto_actual(maximo: int = 4000) -> str:
    try:
        return str(_app().ActiveDocument.Content.Text)[:maximo]

    except Exception:  # noqa: BLE001
        return ""
