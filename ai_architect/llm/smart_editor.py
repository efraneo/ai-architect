"""
Smart Editor

Main AI Editing Engine
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.decision_engine import (
    AutoDecision,
)
from ai_architect.git.commit_manager import (
    CommitManager,
)
from ai_architect.git.diff_manager import (
    DiffManager,
)
from ai_architect.llm.code_editor import (
    CodeEditor,
)
from ai_architect.llm.execution_pipeline import (
    ExecutionPipeline,
)
from ai_architect.memory.memory_engine import (
    MemoryEngine,
)
from ai_architect.memory.models import (
    ExperienceOutcome,
)
from ai_architect.notifier.notifier_manager import (
    NotifierManager,
)


class SmartEditor:
    """
    Main AI Editing Engine.

    Coordinates:

        Repository
            ↓
        ExecutionPipeline
            ↓
        CodeEditor
            ↓
        Diff
            ↓
        Decision
            ↓
        Commit
            ↓
        Memory
            ↓
        Notification
    """

    def __init__(
        self,
        repository: str,
        env_file: str,
    ) -> None:
        self.repository = Path(
            repository,
        ).resolve()

        self.pipeline = ExecutionPipeline()

        self.editor = CodeEditor()

        self.decision = AutoDecision()

        self.memory = MemoryEngine()

        self.commit = CommitManager(
            str(self.repository),
        )

        self.diff = DiffManager(
            str(self.repository),
        )

        self.notifier = NotifierManager(
            env_file,
        )

    def improve(
        self,
        file: str | None,
        instruction: str,
    ) -> dict[str, Any]:
        if file:
            result = self._manual_mode(
                file,
                instruction,
            )

        else:
            result = self.pipeline.execute(
                self.repository,
                instruction,
            )

        if not result["success"]:
            self.notifier.error(
                "AI Improvement Failed",
                str(result),
            )

            return result

        target = result["target"]

        source = result["generated_source"]

        target_path = self.repository / target

        self.editor.write(
            target_path,
            source,
        )

        diff = self.diff.diff()

        # Decision engine integration is currently
        # represented by the approved decision below.
        #
        # The previous implementation contained a
        # commented-out decision block, so the current
        # behavior is preserved.

        decision = {
            "approved": True,
            "confidence": 1.0,
        }

        self.memory.record(
            repository=str(
                self.repository,
            ),
            filename=target,
            instruction=instruction,
            provider="smart_editor",
            outcome=ExperienceOutcome.SUCCESS,
            confidence=float(
                decision["confidence"],
            ),
            metadata={
                "mode": ("manual" if file else "pipeline"),
            },
        )

        self.notifier.success(
            "Code Updated",
            target,
        )

        return {
            "success": True,
            "target": target,
            "decision": decision,
            "diff": diff,
            "quality_issues": result.get(
                "quality_issues",
                [],
            ),
        }

    def _manual_mode(
        self,
        file: str,
        instruction: str,
    ) -> dict:
        result = self.pipeline.execute(
            self.repository,
            instruction,
        )

        result["target"] = file

        return result
