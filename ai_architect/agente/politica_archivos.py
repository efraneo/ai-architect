"""Archivos que el agente no debe leer ni escribir: claves, certificados y credenciales.

Portado de OpenJarvis (`security/file_policy.py`, Apache-2.0), solo la versión en Python.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

DEFAULT_SENSITIVE_PATTERNS: frozenset[str] = frozenset(
    {
        ".env",
        ".env.*",
        "*.env",
        ".secret",
        "*.secrets",
        "credentials.*",
        "*.pem",
        "*.key",
        "*.p12",
        "*.pfx",
        "*.jks",
        "id_rsa",
        "id_ed25519",
        ".htpasswd",
        ".pgpass",
        ".netrc",
    }
)


def is_sensitive_file(path: str | Path) -> bool:
    p = Path(path)
    nombre = p.name
    return any(
        fnmatch.fnmatch(nombre, patron) or fnmatch.fnmatch(str(p), patron)
        for patron in DEFAULT_SENSITIVE_PATTERNS
    )
