"""
=========================================================
Execution Pipeline

Complete Improvement Pipeline
=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.llm.change_validator import (
    ChangeValidator,
)
from ai_architect.llm.code_generator import (
    CodeGenerator,
)
from ai_architect.llm.context_selector import (
    ContextSelector,
)
from ai_architect.llm.improvement_selector import (
    ImprovementSelector,
)
from ai_architect.llm.patch_validator import (
    PatchValidator,
)
from ai_architect.llm.repository_context import (
    RepositoryContext,
)
from ai_architect.llm.repository_scanner import (
    RepositoryScanner,
)


class ExecutionPipeline:
    """
    Complete AI execution pipeline.

    Repository
          │
          ▼
    Scan
          │
          ▼
    Select File
          │
          ▼
    Select Context
          │
          ▼
    Build Prompt
          │
          ▼
    LLM
          │
          ▼
    Validate
          │
          ▼
    Return Result
    """

    def __init__(self) -> None:

        self.scanner = RepositoryScanner()

        self.selector = ImprovementSelector()

        self.context_selector = ContextSelector()

        self.context = RepositoryContext()

        self.generator = CodeGenerator()

        self.patch_validator = PatchValidator()

        self.change_validator = ChangeValidator()

    def execute(
        self,
        repository: str | Path,
        instruction: str,
    ) -> dict[str, Any]:

        repository = Path(repository).resolve()

        target = self.selector.select(
            repository,
        )

        if target is None:
            return {
                "success": False,
                "message": "No editable files found.",
            }

        context_files = self.context_selector.build(
            repository,
            target,
        )

        prompt_context = self.context.build_prompt(
            repository,
            context_files,
        )

        generated = self.generator.generate(
            instruction=instruction,
            context=prompt_context,
        )

        ok, issues = self.patch_validator.validate_source(
            generated,
        )

        if not ok:
            return {
                "success": False,
                "stage": "patch",
                "issues": issues,
            }

        quality = self.change_validator.validate_source(
            generated,
        )

        return {
            "success": True,
            "target": target,
            "context_files": context_files,
            "generated_source": generated,
            "quality_issues": quality,
        }

    def dry_run(
        self,
        repository: str | Path,
    ) -> dict:

        repository = Path(repository)

        return {
            "repository": str(repository),
            "summary": self.scanner.summary(
                repository,
            ),
            "candidate": self.selector.select(
                repository,
            ),
        }
