"""Compatibility and facade helpers for ImprovementEngine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.patch_generator.models import Patch


class ImprovementEngineFacadeMixin:
    """Public helper API kept separate from the orchestration core."""

    @staticmethod
    def summary(analysis: Any) -> dict[str, Any]:
        summary = analysis.summary

        return {
            "total_files": summary.total_files,
            "python_files": summary.python_files,
            "classes": summary.total_classes,
            "functions": summary.total_functions,
            "dependencies": summary.dependency_modules,
            "duplicates": summary.duplicate_groups,
            "complexity": summary.average_complexity,
        }

    @staticmethod
    def recommendations(analysis: Any) -> list[str]:
        return list(analysis.recommendations)

    @staticmethod
    def metrics(analysis: Any) -> dict[str, Any]:
        return dict(analysis.metrics)

    @staticmethod
    def has_recommendations(analysis: Any) -> bool:
        return bool(analysis.recommendations)

    def build_patch(
        self,
        title: str,
        description: str,
        diff: str,
    ) -> Patch:
        patch = self.patch_generator.create(
            title=title,
            description=description,
        )

        self.patch_generator.set_diff(
            patch,
            self._clean_diff(diff),
        )

        self._register_patch_files(
            patch,
            patch.diff,
        )

        return patch

    def validate_patch(
        self,
        patch: Patch,
    ) -> bool:
        return bool(
            self.validator.approved(patch)
        )

    def validate_structure(
        self,
        patch: Patch,
    ) -> bool:
        return bool(
            self.validator.validate_structure(patch)
        )

    def save_patch(
        self,
        patch: Patch,
        repository: Path,
    ) -> Path:
        return self.patch_generator.save(
            patch,
            repository / ".ai_architect",
        )

    @staticmethod
    def patch_summary(
        patch: Patch,
    ) -> dict[str, Any]:
        return {
            "id": patch.id,
            "title": patch.title,
            "approved": patch.approved,
            "files": patch.total_files,
            "created": patch.created_at,
        }

    def provider_summary(self) -> dict[str, Any]:
        return self.provider.summary()

    def provider_available(self) -> bool:
        return bool(
            self.provider.available()
        )

    def generate(
        self,
        prompt: str,
    ) -> str:
        return self.provider.generate(prompt)

    def build_plan(
        self,
        context: Any,
    ) -> Any:
        return self.planner.build_plan(context)

    def plan_summary(
        self,
        plan: Any,
    ) -> dict[str, Any]:
        return self.planner.summary(plan)

    @staticmethod
    def has_tasks(
        plan: Any,
    ) -> bool:
        return bool(
            plan.total_tasks > 0
        )

    def health(self) -> dict[str, Any]:
        components = {
            "analysis": self.analysis is not None,
            "context": self.context_builder is not None,
            "planner": self.planner is not None,
            "provider": self.provider_available(),
            "builder": self.builder is not None,
            "validator": self.validator is not None,
            "writer": self.writer is not None,
        }

        components["healthy"] = all(
            bool(value)
            for value in components.values()
        )

        return components

    def configuration(self) -> dict[str, Any]:
        return {
            "provider": self.provider_summary(),
            "planner": self.planner.__class__.__name__,
            "analysis": self.analysis.__class__.__name__,
            "context_builder": (
                self.context_builder.__class__.__name__
            ),
            "patch_generator": (
                self.patch_generator.__class__.__name__
            ),
            "builder": self.builder.__class__.__name__,
            "validator": self.validator.__class__.__name__,
            "writer": self.writer.__class__.__name__,
        }

    def version(self) -> str:
        return "2.1"

    def ready(self) -> bool:
        return self.provider_available()

    def __call__(
        self,
        repository: str | Path,
        instruction: str | None = None,
        file: str | None = None,
    ) -> dict[str, Any]:
        return self.improve(
            repository,
            instruction=instruction,
            file=file,
        )

    def __repr__(self) -> str:
        provider = self.provider_summary().get(
            "provider",
            "unknown",
        )

        return (
            f"{self.__class__.__name__}"
            f"(provider={provider})"
        )

    def __str__(self) -> str:
        return "QUANT AI Architect Improvement Engine"
