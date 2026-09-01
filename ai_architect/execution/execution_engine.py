"""
Execution Engine

Institutional Execution Engine.

Responsible for validating approved patches and delegating
execution to the execution pipeline.
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.execution.execution_pipeline import ExecutionPipeline
from ai_architect.patch_generator.models import Patch
from ai_architect.patch_generator.patch_validator import PatchValidator


class ExecutionEngine:
    """High-level execution boundary."""

    def __init__(self) -> None:
        self.validator = PatchValidator()
        self.pipeline = ExecutionPipeline()

    def execute(
        self,
        repository: str | Path,
        patch: Patch,
    ) -> dict:
        repository_path = Path(repository).resolve()

        if not self.validate(patch):
            return self._validation_failure(repository_path)

        result = self.pipeline.execute(
            repository_path,
            patch,
        )

        return {
            "success": bool(result.get("success", False)),
            "approved": True,
            "repository": str(repository_path),
            "result": result,
        }

    def dry_run(
        self,
        repository: str | Path,
        patch: Patch,
    ) -> dict:
        repository_path = Path(repository).resolve()

        if not self.validate(patch):
            return {
                **self._validation_failure(repository_path),
                "dry_run": True,
                "files": patch.total_files,
            }

        result = self.pipeline.dry_run(
            repository_path,
            patch,
        )

        return {
            "success": bool(result.get("success", False)),
            "approved": bool(result.get("approved", False)),
            "dry_run": True,
            "repository": str(repository_path),
            "files": patch.total_files,
            "result": result,
        }

    def validate(self, patch: Patch) -> bool:
        """Return whether the patch is explicitly approved for execution."""
        return bool(self.validator.approved(patch))

    @staticmethod
    def _validation_failure(repository: Path) -> dict:
        return {
            "success": False,
            "approved": False,
            "repository": str(repository),
            "message": "Patch validation failed.",
        }

    def pipeline_summary(self) -> dict:
        return self.pipeline.summary()

    def health(self) -> dict:
        pipeline_health = self.pipeline.health()
        healthy = bool(pipeline_health.get("healthy", False))

        return {
            "validator": True,
            "pipeline": healthy,
            "healthy": healthy,
        }

    def configuration(self) -> dict:
        return {
            "validator": self.validator.__class__.__name__,
            "pipeline": self.pipeline.__class__.__name__,
            "pipeline_configuration": self.pipeline.configuration(),
        }

    def statistics(self) -> dict:
        pipeline_health = self.pipeline.health()

        return {
            "validator": self.validator.__class__.__name__,
            "pipeline": self.pipeline.__class__.__name__,
            "pipeline_statistics": self.pipeline.statistics(),
            "healthy": bool(
                pipeline_health.get("healthy", False),
            ),
        }

    def version(self) -> str:
        return "2.1"

    def ready(self) -> bool:
        return self.pipeline.ready()

    def supports_dry_run(self) -> bool:
        return True

    def supports_patch_validation(self) -> bool:
        return True

    def patch_summary(self, patch: Patch) -> dict:
        return {
            "id": patch.id,
            "title": patch.title,
            "description": patch.description,
            "approved": patch.approved,
            "files": patch.total_files,
            "created": patch.created_at,
        }

    def patch_valid(self, patch: Patch) -> bool:
        return self.validate(patch)

    def patch_files(self, patch: Patch) -> list:
        return list(patch.files)

    def patch_count(self, patch: Patch) -> int:
        return patch.total_files

    def execute_pipeline(
        self,
        repository: str | Path,
        patch: Patch,
    ) -> dict:
        """Execute only through the same approval boundary as execute()."""

        return self.execute(
            repository,
            patch,
        )

    def rollback(
        self,
        repository: str | Path,
        patch: Patch,
    ) -> dict:
        """
        Roll back an approved patch.

        Rollback is deliberately kept behind the same approval boundary.
        """

        repository_path = Path(repository).resolve()

        if not self.validate(patch):
            return self._validation_failure(repository_path)

        return self.pipeline.rollback(
            repository_path,
            patch,
        )

    def verify(self, repository: str | Path) -> bool:
        return self.pipeline.verify(
            Path(repository).resolve(),
        )

    def pipeline_ready(self) -> bool:
        return self.pipeline.ready()

    def export(self, result: dict) -> dict:
        return dict(result)

    def summary(self, result: dict) -> dict:
        return {
            "success": bool(result.get("success", False)),
            "approved": bool(result.get("approved", False)),
            "repository": result.get("repository"),
        }

    def diagnostics(self) -> dict:
        return {
            "engine": self.__class__.__name__,
            "pipeline": self.pipeline.__class__.__name__,
            "validator": self.validator.__class__.__name__,
            "pipeline_diagnostics": self.pipeline.diagnostics(),
        }

    def reset(self) -> None:
        self.validator = PatchValidator()
        self.pipeline = ExecutionPipeline()

    def __call__(
        self,
        repository: str | Path,
        patch: Patch,
    ) -> dict:
        return self.execute(
            repository,
            patch,
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(pipeline={self.pipeline.__class__.__name__})"
        )

    def __str__(self) -> str:
        return "QUANT AI Architect Execution Engine"
