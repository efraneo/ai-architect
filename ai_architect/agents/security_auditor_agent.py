"""
=========================================================
Security Auditor Agent
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .base_agent import BaseAgent


class SecurityAuditorAgent(BaseAgent):
    name = "Security Auditor"

    TOKENS = (
        "secret",
        "token",
        "apikey",
        "password",
        "private_key",
    )

    def review(
        self,
        project: str,
    ) -> dict:

        alerts = []

        for file in Path(project).rglob("*"):
            if not file.is_file():
                continue

            try:
                text = file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).lower()

            except Exception:
                continue

            for token in self.TOKENS:
                if token in text:
                    alerts.append(
                        {
                            "file": str(file),
                            "keyword": token,
                        }
                    )

        return {
            "alerts": alerts,
            "total": len(alerts),
        }
