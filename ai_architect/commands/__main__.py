"""
Commands CLI.

Institutional Command Dispatcher.
"""

from __future__ import annotations

import argparse
import json

from ai_architect.commands.analyze import run as analyze
from ai_architect.commands.doctor import run as doctor
from ai_architect.commands.execute import run as execute
from ai_architect.commands.improve import run as improve
from ai_architect.commands.review import run as review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="architect",
        description="QUANT AI Architect Command Line Interface",
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # -------------------------------------------------
    # analyze
    # -------------------------------------------------

    analyze_parser = sub.add_parser(
        "analyze",
        help="Analyze a repository.",
    )

    analyze_parser.add_argument(
        "project",
        help="Repository path.",
    )

    # -------------------------------------------------
    # review
    # -------------------------------------------------

    review_parser = sub.add_parser(
        "review",
        help="Review a repository.",
    )

    review_parser.add_argument(
        "project",
        help="Repository path.",
    )

    # -------------------------------------------------
    # improve
    # -------------------------------------------------

    improve_parser = sub.add_parser(
        "improve",
        help="Generate repository improvements.",
    )

    improve_parser.add_argument(
        "project",
        help="Repository path.",
    )

    improve_parser.add_argument(
        "--file",
        default=None,
        help="Optional file to target.",
    )

    improve_parser.add_argument(
        "--instruction",
        default=None,
        help="Optional improvement instruction.",
    )

    # -------------------------------------------------
    # execute
    # -------------------------------------------------

    execute_parser = sub.add_parser(
        "execute",
        help="Execute a validated patch.",
    )

    execute_parser.add_argument(
        "project",
        help="Repository path.",
    )

    execute_parser.add_argument(
        "patch",
        help="Patch path.",
    )

    execute_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and simulate execution without applying changes.",
    )

    # -------------------------------------------------
    # doctor
    # -------------------------------------------------

    sub.add_parser(
        "doctor",
        help="Run system diagnostics.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        result = analyze(
            args.project,
        )

    elif args.command == "review":
        result = review(
            args.project,
        )

    elif args.command == "improve":
        result = improve(
            project=args.project,
            file=args.file,
            instruction=args.instruction,
        )

    elif args.command == "execute":
        result = execute(
            project=args.project,
            patch=args.patch,
            dry_run=args.dry_run,
        )

    elif args.command == "doctor":
        result = doctor()

    else:
        parser.error("Unknown command.")
        return

    print(
        json.dumps(
            result,
            indent=4,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
