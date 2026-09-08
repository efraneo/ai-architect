"""Descripciones de herramientas. OpenJarvis permite sobreescribirlas desde disco; aquí no hace falta."""

from __future__ import annotations


def get_tool_description_override(
    nombre: str,
) -> str | None:  # noqa: ARG001 - misma firma que el original
    return None
