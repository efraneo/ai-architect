"""
Execution Worker.
"""

from __future__ import annotations

import traceback
from typing import Any


class ExecutionWorker:
    def execute(
        self,
        task: dict[str, Any],
    ) -> dict[str, object]:
        try:
            callback = task["callback"]

            if not callable(callback):
                raise TypeError("Task callback must be callable.")

            result = callback()

            return {
                "success": True,
                "result": result,
            }

        except Exception:
            return {
                "success": False,
                "traceback": traceback.format_exc(),
            }
