"""
=========================================================
Embeddings
=========================================================
"""

from __future__ import annotations

import hashlib


class Embeddings:
    def encode(
        self,
        text: str,
    ) -> str:

        return hashlib.sha256(text.encode()).hexdigest()
