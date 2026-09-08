"""El archivo que se entrega: documento, tabla o gráfica montados en HTML (y SVG) bien formado.

``crear`` reexporta estos nombres."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from ai_architect.core import perfil


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
