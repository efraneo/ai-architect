"""
=========================================================
QUANT AI Architect CLI
=========================================================
"""

from __future__ import annotations

import argparse
import json
import sys

from ai_architect.commands import (
    analyze,
    doctor,
    execute,
    improve,
    review,
)


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="ai-architect",
        description="QUANT AI Architect",
    )

    parser.add_argument(
        "command",
        choices=[
            "analyze",
            "review",
            "improve",
            "execute",
            "doctor",
        ],
    )

    parser.add_argument(
        "project",
        nargs="?",
        default=".",
        help="Project directory",
    )

    parser.add_argument(
        "--file",
        default=None,
        help="Target file for improve command",
    )

    parser.add_argument(
        "--patch",
        default=None,
        help="Patch file for execute command",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate an execution patch without modifying files",
    )

    parser.add_argument(
        "--instruction",
        default="Improve code quality",
        help="Instruction for improve command",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print result as JSON",
    )

    return parser


def print_result(
    result,
    as_json: bool,
):

    if as_json:
        print(
            json.dumps(
                result,
                indent=4,
                default=str,
            )
        )

        return

    if isinstance(result, dict):
        for key, value in result.items():
            print(f"{key}: {value}")

        return

    print(result)


def main():

    parser = build_parser()

    args = parser.parse_args()

    # =====================================================
    # Doctor
    # =====================================================

    if args.command == "doctor":
        result = doctor.run()

    # =====================================================
    # Analyze
    # =====================================================

    elif args.command == "analyze":
        result = analyze.run(
            args.project,
        )

    # =====================================================
    # Review
    # =====================================================

    elif args.command == "review":
        result = review.run(
            args.project,
        )

    # =====================================================
    # Improve
    # =====================================================

    elif args.command == "improve":
        result = improve.run(
            args.project,
            file=args.file,
            instruction=args.instruction,
        )

    # =====================================================
    # Execute
    # =====================================================

    elif args.command == "execute":
        if not args.patch:
            parser.error("execute requires --patch <patch_file>")

        result = execute.run(
            project=args.project,
            patch=args.patch,
            dry_run=args.dry_run,
        )

    # =====================================================
    # Safety fallback
    # =====================================================

    else:
        parser.error("Unknown command.")

    print_result(
        result,
        args.json,
    )


if __name__ == "__main__":
    sys.exit(main())
