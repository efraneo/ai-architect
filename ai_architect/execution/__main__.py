"""
=========================================================
Execution Module

Standalone Execution Entry Point

=========================================================
"""

from __future__ import annotations

import argparse
import json

from ai_architect.execution.execution_engine import (
    ExecutionEngine,
)
from ai_architect.patch_generator.patch_loader import (
    PatchLoader,
)


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="execution",
        description=("QUANT AI Architect Execution Module"),
    )

    parser.add_argument(
        "project",
    )

    parser.add_argument(
        "patch",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    return parser


########################################################


def main() -> None:

    args = build_parser().parse_args()

    engine = ExecutionEngine()

    loader = PatchLoader()

    patch = loader.load(
        args.patch,
    )

    if args.dry_run:
        result = engine.dry_run(
            args.project,
            patch,
        )

    else:
        result = engine.execute(
            args.project,
            patch,
        )

    # Parte 2

    print(
        json.dumps(
            result,
            indent=4,
            default=str,
        )
    )


########################################################


if __name__ == "__main__":
    main()
