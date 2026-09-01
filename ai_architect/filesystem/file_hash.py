"""
===========================================================
QUANT TITAN AI ARCHITECT

filesystem/file_hash.py

Generador de hashes.

Usado para:

- Workspace Cache
- Change Detector
- Repository
- Incremental Analyzer

===========================================================
"""

from __future__ import annotations

import hashlib
from pathlib import Path


class FileHash:
    """
    Calcula hashes SHA256.
    """

    BLOCK_SIZE = 65536

    def sha256(self, path: Path) -> str:

        sha = hashlib.sha256()

        with path.open("rb") as file:
            while True:
                block = file.read(self.BLOCK_SIZE)

                if not block:
                    break

                sha.update(block)

        return sha.hexdigest()

    def compare(self, first: Path, second: Path) -> bool:

        return self.sha256(first) == self.sha256(second)
