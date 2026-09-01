"""
=========================================================
Prompt Builder
=========================================================
"""

from __future__ import annotations


class PromptBuilder:
    def system_prompt(self) -> str:

        return """
You are QUANT AI ARCHITECT.

Rules:

- Never generate files over 600 lines.
- Preserve architecture.
- Prefer refactoring over rewriting.
- Remove duplicated code.
- Improve readability.
- Execute changes incrementally.
- Never break public APIs.
- Produce deterministic output.
"""

    def code_review_prompt(
        self,
        source: str,
    ) -> str:

        return f"""
Review this code.

Objectives:

- Detect bugs
- Detect duplicated logic
- Detect architecture violations
- Suggest SOLID improvements
- Suggest performance improvements

Code:

{source}
"""

    def refactor_prompt(
        self,
        source: str,
    ) -> str:

        return f"""
Refactor this code.

Requirements:

- Maximum 600 lines/file
- Keep functionality
- Improve architecture
- Remove duplicated code
- Improve typing
- Improve comments

Code:

{source}
"""

    def improvement_prompt(
        self,
        project_summary: str,
    ) -> str:

        return f"""
Analyze the project.

Project summary:

{project_summary}

Generate:

1. Problems
2. Risks
3. Improvements
4. Refactor plan
5. Execution order
"""
