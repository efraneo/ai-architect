"""
=========================================================
Texto

Comparar frases dichas en voz alta.
=========================================================

Lo que llega de un micrófono no viene como se escribiría. Whisper pone
tildes donde quiere, decide por su cuenta si va con signos de interrogación
y unas veces escribe "¿Qué hora es?" y otras "que hora es". Comparar eso en
crudo falla siempre.

Aquí se reduce todo a lo comparable: minúsculas, sin tildes, sin signos y
con un solo espacio entre palabras.
"""

from __future__ import annotations

import unicodedata


def sin_adornos(texto: str) -> str:
    """El texto reducido a letras, números y espacios simples."""
    plano = unicodedata.normalize("NFKD", str(texto).lower())

    # NFKD separa la tilde de la letra, así que descartar lo que no es
    # alfanumérico quita los acentos sin tener que listarlos.
    letras = [c for c in plano if c.isalnum() or c.isspace()]

    return " ".join("".join(letras).split())


def contiene(frase: str, *claves: str) -> bool:
    """Si la frase, ya limpia, contiene alguna de las claves."""
    limpia = sin_adornos(frase)

    return any(sin_adornos(clave) in limpia for clave in claves)
