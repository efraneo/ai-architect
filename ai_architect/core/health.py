"""
=========================================================
Health Monitor
=========================================================
"""

from __future__ import annotations

from datetime import datetime


class Health:
    def __init__(self):

        self.components = {}

        self.started = datetime.utcnow()

    def register(
        self,
        component,
    ):

        self.components[component.name] = component

    def report(self):

        result = {}

        healthy = True

        for component in self.components.values():
            try:
                info = component.health()

            except Exception as exc:
                info = {
                    "status": "ERROR",
                    "error": str(exc),
                }

                healthy = False

            result[component.name] = info

        return {
            "started": self.started.isoformat(),
            "healthy": healthy,
            "components": result,
        }
