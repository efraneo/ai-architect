"""
=========================================================
Improve Command

Institutional Improve Command
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.improver.improvement_engine import ImprovementEngine


def run(
    project: str,
    file: str | None = None,
    instruction: str | None = None,
    apply: bool = False,
) -> dict:
    """
    Run the improvement command against a repository.
    """

    repository = Path(project).resolve()

    if not repository.exists():
        return {
            "success": False,
            "repository": str(repository),
            "error": "Repository not found.",
        }

    if not repository.is_dir():
        return {
            "success": False,
            "repository": str(repository),
            "error": "Project path is not a directory.",
        }

    try:
        engine = ImprovementEngine()

        return engine.improve(
            str(repository),
            instruction=instruction,
            file=file,
            apply=apply,
        )

    except Exception as exc:
        return {
            "success": False,
            "repository": str(repository),
            "error": str(exc),
        }


###############################################################
# Information
###############################################################


def info() -> dict:
    engine = ImprovementEngine()

    return {
        "command": "improve",
        "description": (
            "Automatically analyzes the project and generates an improvement patch."
        ),
        "provider": engine.provider_summary(),
        "ready": engine.ready(),
    }


###############################################################
# Health
###############################################################


def health() -> dict:
    return ImprovementEngine().health()


###############################################################
# Version
###############################################################


def version() -> str:
    return ImprovementEngine().version()


###############################################################
# Convenience
###############################################################


def __call__(
    project: str,
    file: str | None = None,
    instruction: str | None = None,
) -> dict:
    return run(
        project=project,
        file=file,
        instruction=instruction,
    )


###############################################################
# CLI Metadata
###############################################################

COMMAND = {
    "name": "improve",
    "help": (
        "Analyze the repository, "
        "generate an execution plan "
        "and produce an improvement patch."
    ),
}


###############################################################
# Debug
###############################################################

if __name__ == "__main__":
    import json

    print(
        json.dumps(
            run("."),
            indent=4,
            default=str,
        )
    )
