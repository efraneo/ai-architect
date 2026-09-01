"""
=========================================================
Agents Command

CLI adapter for the multi-agent orchestrator.
=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.agents.agent_manager import AgentManager


def run(
    project: str,
    ai: bool = False,
) -> dict:
    """
    Runs the agents over a repository.

    By default only the static agents run: metrics, architecture, testing,
    security, dependencies, licences and git. They cost nothing and need no
    API key.

    With ``ai=True`` the five AI agents run as well -- architect, refactor,
    reviewer, tests and documentation -- which means five provider calls.
    That is opt-in, so nobody spends money without asking for it.

    Parameters
    ----------
    project:
        Repository root.
    ai:
        Also run the AI agents.

    Returns
    -------
    dict
        Serializable report.
    """

    repository = Path(
        project,
    ).resolve()

    if not repository.exists():
        return {
            "success": False,
            "repository": str(repository),
            "error": "Repository not found.",
        }

    manager = AgentManager()

    try:
        if ai:
            context = manager.execute(
                str(repository),
            )

            data: dict[str, Any] = context.data

        else:
            data = manager.inspect(
                str(repository),
            )

    except Exception as exc:
        return {
            "success": False,
            "repository": str(repository),
            "error": str(exc),
        }

    findings = manager.findings_de(data)

    return {
        "success": True,
        "repository": str(repository),
        "ai": ai,
        "agents": sorted(data.keys()),
        "verdict": manager.veredicto(data),
        "total_findings": len(findings),
        "findings": findings,
        "data": data,
    }
