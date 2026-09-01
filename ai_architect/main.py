"""
=========================================================
QUANT AI ARCHITECT

Entry Point
=========================================================
"""

from ai_architect.engine import (
    ArchitectEngine,
)

PROJECT = "../QUANT_TITAN_PRO"

TELEGRAM = "../telegram_quant_titan.env"


def main():

    engine = ArchitectEngine(
        project=PROJECT,
        telegram_env=TELEGRAM,
    )

    engine.execute()


if __name__ == "__main__":
    main()
