from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent


class LicenseAgent(BaseAgent):
    name = "License Agent"

    LICENSE_FILES = [
        "LICENSE",
        "LICENSE.txt",
        "LICENSE.md",
        "COPYING",
        "NOTICE",
    ]

    LICENSE_PATTERNS = {
        "MIT": [
            "mit license",
            "permission is hereby granted",
        ],
        "Apache-2.0": [
            "apache license",
            "version 2.0",
        ],
        "GPL-3.0": [
            "gnu general public license",
            "version 3",
        ],
        "BSD-3-Clause": [
            "redistribution and use",
            "neither the name",
        ],
        "Mozilla-2.0": [
            "mozilla public license",
        ],
        "ISC": [
            "isc license",
        ],
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

        detected: list[str] = []
        files: list[str] = []

        for filename in self.LICENSE_FILES:
            file = project_path / filename

            if not file.exists():
                continue

            files.append(str(file))

            try:
                content = file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).lower()

            except Exception:
                continue

            for license_name, patterns in self.LICENSE_PATTERNS.items():
                if all(pattern in content for pattern in patterns):
                    detected.append(license_name)

        detected = sorted(set(detected))

        return {
            "agent": self.name,
            "license_files": files,
            "licenses": detected,
            "detected": bool(detected),
            "status": "OK" if detected else "UNKNOWN",
        }

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "licencias",
            "License Detection",
            "Compliance Check",
            "Open Source Analysis",
            "License Inventory",
            "Repository Compliance",
        ]
