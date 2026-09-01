"""
Doctor Command.
"""

from __future__ import annotations

import platform
import sys
from typing import Any


def run() -> dict[str, Any]:
    return {
        "success": True,
        "python": sys.version,
        "platform": platform.platform(),
        "status": "healthy",
    }
