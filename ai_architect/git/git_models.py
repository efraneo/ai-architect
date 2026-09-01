"""
=========================================================
Git Models

Lo que devuelve git, con forma.
=========================================================

Venían de ``repository/``, la capa de git paralela que solo era alcanzable
desde ``agent.py`` -- que no importaba nadie. Es lo único que esa capa tenía
y ``git/`` no: un estado con forma en vez de una cadena que hay que volver a
parsear en cada sitio.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GitStatus:
    """El estado del árbol de trabajo, ya interpretado."""

    branch: str = ""

    modified: list[str] = field(default_factory=list)

    created: list[str] = field(default_factory=list)

    deleted: list[str] = field(default_factory=list)

    renamed: list[str] = field(default_factory=list)

    untracked: list[str] = field(default_factory=list)

    conflicted: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        """¿No hay nada pendiente?

        Antes era un campo que se calculaba al construir y se podía quedar
        desfasado si alguien tocaba las listas. Ahora se deduce.
        """
        return not (
            self.modified
            or self.created
            or self.deleted
            or self.renamed
            or self.untracked
            or self.conflicted
        )

    @property
    def total(self) -> int:
        return (
            len(self.modified)
            + len(self.created)
            + len(self.deleted)
            + len(self.renamed)
            + len(self.untracked)
            + len(self.conflicted)
        )

    def as_dict(self) -> dict[str, object]:
        """Para el informe de los agentes, que va a JSON."""
        return {
            "branch": self.branch,
            "modified": self.modified,
            "created": self.created,
            "deleted": self.deleted,
            "renamed": self.renamed,
            "untracked": self.untracked,
            "conflicted": self.conflicted,
            "clean": self.clean,
            "total": self.total,
        }
