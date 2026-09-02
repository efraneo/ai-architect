from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base_agent import BaseAgent
from .scope import archivos


class SecurityAgent(BaseAgent):
    name = "Security Agent"

    SECRET_PATTERNS = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "GitHub Token": r"ghp_[A-Za-z0-9]{36}",
        "OpenAI Key": r"sk-[A-Za-z0-9]{20,}",
        "Password Assignment": r"password\s*=\s*['\"].+['\"]",
        "Private Key": r"-----BEGIN .*PRIVATE KEY-----",
    }

    def run(
        self,
        context,
    ):
        return self.review(
            context,
        )

    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        project_path = Path(project)

        findings: list[dict[str, str]] = []

        scanned = 0

        # Its own pattern table matches its own patterns: scanning itself
        # reports a leaked private key on every repository that ships this
        # scanner -- starting with this one.
        yo = Path(__file__).resolve()

        for file in archivos(project_path):
            if file.resolve() == yo:
                continue

            scanned += 1

            try:
                text = file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

            except Exception:
                continue

            for name, pattern in self.SECRET_PATTERNS.items():
                if re.search(
                    pattern,
                    text,
                    re.MULTILINE,
                ):
                    findings.append(
                        {
                            "file": str(file),
                            "issue": name,
                        }
                    )

        # El historial, que es lo que de verdad quema. Un secreto en el
        # disco se arregla borrandolo; uno commiteado sigue ahi despues de
        # borrarlo, lo tiene quien clono y hay que rotarlo. Dos problemas
        # distintos que hasta ahora se contaban igual.
        from ai_architect.herramientas import historial

        pasado = historial.revisar(project)

        quemados = pasado["hallazgos"]

        return {
            "agent": self.name,
            "files_scanned": scanned,
            "findings": findings
            + [
                {
                    "file": f"historial (commit {h['commit']})",
                    "type": h["tipo"],
                    "severity": "CRITICAL",
                    "detail": h["muestra"],
                }
                for h in quemados
            ],
            "history_reviewed": pasado["revisados"],
            "history_note": pasado["nota"],
            "history_summary": historial.resumen(pasado),
            "security_score": max(
                0,
                100 - len(findings) * 10 - len(quemados) * 20,
            ),
            "status": "OK" if not findings and not quemados else "WARN",
        }

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "seguridad",
            "secretos y contrasenas en el codigo",
            "secretos commiteados en el historial",
            "claves y tokens expuestos",
        ]
