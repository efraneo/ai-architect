"""State and compatibility helpers for the execution pipeline."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ai_architect.patch_generator.models import Patch


class ExecutionPipelineStateMixin:
    """Public state, diagnostics, and compatibility API.

    This mixin is only used through :class:`ExecutionPipeline`, which is what
    defines the counters and the operations below. Declaring them here, under
    ``TYPE_CHECKING``, tells the type checker what the mixin may rely on
    without adding anything at runtime.
    """

    executed_files: int
    failed_files: int
    last_result: dict[str, Any]

    if TYPE_CHECKING:  # pragma: no cover

        def verify(self, repository: str | Path) -> bool: ...

        def execute(self, repository: str | Path, patch: Patch) -> dict: ...

    def exists(self, repository: str | Path) -> bool:
        return self.verify(repository)

    def summary(self) -> dict:
        return {
            "executed": self.executed_files,
            "failed": self.failed_files,
            "healthy": self.failed_files == 0,
            "last_result": dict(self.last_result),
        }

    def reset(self) -> None:
        self.executed_files = 0
        self.failed_files = 0
        self.last_result = {}

    def statistics(self) -> dict:
        return {
            "executed": self.executed_files,
            "failed": self.failed_files,
            "total": self.executed_files + self.failed_files,
        }

    def health(self) -> dict:
        return {
            "healthy": self.failed_files == 0,
            "executed": self.executed_files,
            "failed": self.failed_files,
        }

    def configuration(self) -> dict:
        return {
            "atomic_write": False,
            "rollback": True,
            "verification": True,
            "git_apply": True,
            "preflight_check": True,
        }

    def ready(self) -> bool:
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except (FileNotFoundError, OSError):
            return False

        return result.returncode == 0

    def supports_rollback(self) -> bool:
        return True

    def supports_verification(self) -> bool:
        return True

    def supports_atomic_write(self) -> bool:
        return False

    def diagnostics(self) -> dict:
        return {
            "engine": self.__class__.__name__,
            "ready": self.ready(),
            "supports_rollback": self.supports_rollback(),
            "supports_verification": self.supports_verification(),
            "supports_atomic_write": self.supports_atomic_write(),
            "git_apply": True,
        }

    def version(self) -> str:
        return "2.1"

    def export(self) -> dict:
        return {
            "executed": self.executed_files,
            "failed": self.failed_files,
            "configuration": self.configuration(),
            "last_result": dict(self.last_result),
        }

    def import_state(self, state: dict) -> None:
        self.executed_files = int(state.get("executed", 0))
        self.failed_files = int(state.get("failed", 0))
        self.last_result = dict(state.get("last_result", {}))

    def executed(self) -> int:
        return self.executed_files

    def failed(self) -> int:
        return self.failed_files

    def total(self) -> int:
        return self.executed_files + self.failed_files

    def success(self) -> bool:
        return (
            self.failed_files == 0
            and bool(self.last_result)
            and bool(self.last_result.get("success", False))
        )

    def empty(self) -> bool:
        return self.total() == 0

    def __call__(
        self,
        repository: str | Path,
        patch: Patch,
    ) -> dict:
        return self.execute(repository, patch)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"executed={self.executed_files}, "
            f"failed={self.failed_files})"
        )

    def __str__(self) -> str:
        return "QUANT AI Architect Execution Pipeline"
