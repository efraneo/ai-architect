"""Un ``.docx`` sin librerías: es un ZIP con tres XML dentro.

``crear`` reexporta estos nombres."""

from __future__ import annotations

import io

from ai_architect.commands.crear_html import _escapar

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
