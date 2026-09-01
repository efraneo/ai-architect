"""
=========================================================
Core Exceptions

Shared Exceptions
=========================================================
"""

from __future__ import annotations


class AIArchitectError(Exception):
    """
    Base exception.
    """


class ValidationError(
    AIArchitectError,
):
    """
    Validation failed.
    """


class ExecutionError(
    AIArchitectError,
):
    """
    Execution failed.
    """


class PlanningError(
    AIArchitectError,
):
    """
    Planner error.
    """


class DecisionError(
    AIArchitectError,
):
    """
    Decision engine error.
    """


class ProviderError(
    AIArchitectError,
):
    """
    LLM provider error.
    """


class RepositoryError(
    AIArchitectError,
):
    """
    Repository operation error.
    """


class AgentError(
    AIArchitectError,
):
    """
    Agent execution error.
    """


class MemorySubsystemError(
    AIArchitectError,
):
    """
    Memory subsystem error.

    Se llamaba ``MemoryError``, que es el nombre de una excepción **interna
    de Python**. Cualquiera que la importara aquí y luego escribiera
    ``except MemoryError`` estaría capturando la equivocada: un
    agotamiento de memoria real pasaría de largo.
    """
