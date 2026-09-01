"""
QUANT TITAN AI ARCHITECT

filesystem/file_loader.py

Responsabilidad

Carga archivos del proyecto.

Nunca analiza.

Nunca modifica.

Solo lee.

Soporta:

- Python
- YAML
- JSON
- TOML
- Texto
===========================================================
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any, cast

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


class FileLoader:
    """
    Cargador universal de archivos.
    """

    TEXT_EXTENSIONS = {
        ".py",
        ".txt",
        ".md",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
    }

    def read_text(
        self,
        path: Path,
        encoding: str = "utf-8",
    ) -> str:
        return path.read_text(
            encoding=encoding,
        )

    def read_bytes(
        self,
        path: Path,
    ) -> bytes:
        return path.read_bytes()

    def load_json(
        self,
        path: Path,
    ) -> dict[str, Any]:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return cast(
            dict[str, Any],
            data,
        )

    def load_yaml(
        self,
        path: Path,
    ) -> dict[str, Any]:
        if yaml is None:
            raise RuntimeError(
                "PyYAML no está instalado.",
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = yaml.safe_load(file)

        return cast(
            dict[str, Any],
            data,
        )

    def load_toml(
        self,
        path: Path,
    ) -> dict[str, Any]:
        with path.open(
            "rb",
        ) as file:
            return tomllib.load(file)

    def exists(
        self,
        path: Path,
    ) -> bool:
        return path.exists()

    def size(
        self,
        path: Path,
    ) -> int:
        return path.stat().st_size
