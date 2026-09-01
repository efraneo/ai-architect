"""
=========================================================
Prompt Library

Centralized Prompt Templates
=========================================================
"""

from __future__ import annotations

from textwrap import dedent


class PromptLibrary:
    """
    Biblioteca centralizada de prompts.

    Todos los prompts utilizados por el AI Architect
    deben construirse aquí para mantener consistencia
    entre proveedores LLM.
    """

    SYSTEM_PROMPT = dedent(
        """
        You are QUANT AI Architect.

        You are an expert software architect.

        Your responsibilities are:

        - Improve existing code.
        - Never invent project APIs.
        - Respect the current architecture.
        - Produce minimal changes.
        - Preserve formatting whenever possible.
        - Never remove functionality.
        - Return ONLY valid source code.
        """
    ).strip()

    def improve_code(
        self,
        instruction: str,
        repository_context: str,
    ) -> str:

        return dedent(
            f"""
            {self.SYSTEM_PROMPT}

            =====================================================
            REPOSITORY CONTEXT
            =====================================================

            {repository_context}

            =====================================================
            TASK
            =====================================================

            {instruction}

            =====================================================
            RULES
            =====================================================

            1. Modify only the requested file.
            2. Preserve imports when possible.
            3. Avoid breaking existing APIs.
            4. Produce clean Python code.
            5. Return ONLY the final file.
            """
        ).strip()

    def review_code(
        self,
        source: str,
    ) -> str:

        return dedent(
            f"""
            {self.SYSTEM_PROMPT}

            Review the following Python source code.

            Detect:

            - bugs
            - dead code
            - duplicated logic
            - complexity
            - security issues

            Return a structured review.

            SOURCE

            {source}
            """
        ).strip()

    def explain_code(
        self,
        source: str,
    ) -> str:

        return dedent(
            f"""
            {self.SYSTEM_PROMPT}

            Explain this code.

            Focus on:

            - architecture
            - responsibilities
            - dependencies
            - possible improvements

            SOURCE

            {source}
            """
        ).strip()

    def refactor_code(
        self,
        source: str,
        objective: str,
    ) -> str:

        return dedent(
            f"""
            {self.SYSTEM_PROMPT}

            Refactor the following code.

            Objective:

            {objective}

            Constraints:

            - preserve behavior
            - improve readability
            - reduce complexity
            - keep public API unchanged

            SOURCE

            {source}

            Return ONLY the refactored source.
            """
        ).strip()
