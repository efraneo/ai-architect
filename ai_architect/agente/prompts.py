"""Sobreescrituras de prompts por agente. OpenJarvis las lee de ~/.openjarvis; aquí no se usan."""

from __future__ import annotations

from typing import Any


def load_system_prompt_override(agent_name: str) -> str | None:  # noqa: ARG001
    return None


def load_few_shot_exemplars(agent_name: str) -> list[dict[str, Any]]:  # noqa: ARG001
    return []
