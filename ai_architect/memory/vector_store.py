"""
=========================================================
Vector Store
=========================================================
"""

from __future__ import annotations

from hashlib import sha256


class VectorStore:
    def embedding(
        self,
        text: str,
    ) -> str:

        return sha256(text.encode()).hexdigest()

    def similarity(
        self,
        a: str,
        b: str,
    ) -> float:

        if a == b:
            return 1.0

        common = len(set(a) & set(b))

        return common / max(
            len(set(a + b)),
            1,
        )
