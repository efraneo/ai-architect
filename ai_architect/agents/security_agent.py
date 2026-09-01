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

        return {
            "agent": self.name,
            "files_scanned": scanned,
            "findings": findings,
            "security_score": max(
                0,
                100 - len(findings) * 10,
            ),
            "status": "OK" if not findings else "WARN",
        }

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "Secret Detection",
            "Credential Scan",
            "Token Detection",
            "Private Key Detection",
            "Basic Security Audit",
        ]
