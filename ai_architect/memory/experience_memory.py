"""
=========================================================
Experience Memory

Persistent Experience Repository
=========================================================
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ai_architect.memory.experience import Experience


class ExperienceMemory:
    """
    Persistent repository of execution experiences.

    Stores successful and failed executions so they can
    be reused by future planning and decision engines.
    """

    FILE_NAME = ".quant_experience.json"

    def __init__(
        self,
        repository: str,
    ) -> None:

        self.repository = Path(repository)

        self.file = self.repository / self.FILE_NAME

        self.experiences = self._load()

    # -----------------------------------------------------

    def _load(
        self,
    ) -> list[Experience]:

        if not self.file.exists():
            return []

        try:
            with self.file.open(
                "r",
                encoding="utf-8",
            ) as f:
                raw = json.load(f)

        except Exception:
            return []

        return [Experience.from_dict(item) for item in raw]

    # -----------------------------------------------------

    def save(
        self,
    ) -> None:

        with self.file.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                [exp.to_dict() for exp in self.experiences],
                f,
                indent=4,
                ensure_ascii=False,
            )

    # -----------------------------------------------------

    def add(
        self,
        experience: Experience,
    ) -> None:

        self.experiences.append(
            experience,
        )

        self.save()

    # -----------------------------------------------------

    def create(
        self,
        *,
        project: str,
        task: str,
        decision: str,
        success: bool,
        confidence: float,
        duration: float,
        notes: str = "",
        quality: float = 0.0,
        provider: str = "",
        model: str = "",
        commit: str = "",
        retries: int = 0,
        metadata: dict | None = None,
    ) -> Experience:

        experience = Experience(
            timestamp=datetime.utcnow(),
            project=project,
            task=task,
            decision=decision,
            success=success,
            confidence=confidence,
            duration=duration,
            notes=notes,
            quality=quality,
            provider=provider,
            model=model,
            commit=commit,
            retries=retries,
            metadata=metadata,
        )

        self.add(
            experience,
        )

        return experience

    # -----------------------------------------------------

    def all(
        self,
    ) -> list[Experience]:

        return list(
            self.experiences,
        )

    # -----------------------------------------------------

    def successful(
        self,
    ) -> list[Experience]:

        return [exp for exp in self.experiences if exp.success]

    # -----------------------------------------------------

    def failed(
        self,
    ) -> list[Experience]:

        return [exp for exp in self.experiences if not exp.success]

    # -----------------------------------------------------

    def search(
        self,
        keyword: str,
    ) -> list[Experience]:

        keyword = keyword.lower()

        return [
            exp
            for exp in self.experiences
            if keyword in exp.task.lower() or keyword in exp.notes.lower()
        ]

    # -----------------------------------------------------

    def best(
        self,
        minimum_quality: float = 90.0,
    ) -> list[Experience]:

        return sorted(
            [exp for exp in self.successful() if exp.quality >= minimum_quality],
            key=lambda x: x.quality,
            reverse=True,
        )

    # -----------------------------------------------------

    def last(
        self,
        limit: int = 10,
    ) -> list[Experience]:

        return self.experiences[-limit:]

    # -----------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        total = len(
            self.experiences,
        )

        successful = len(
            self.successful(),
        )

        failed = len(
            self.failed(),
        )

        if total == 0:
            average_confidence = 0.0

            average_quality = 0.0

        else:
            average_confidence = sum(exp.confidence for exp in self.experiences) / total

            average_quality = sum(exp.quality for exp in self.experiences) / total

        return {
            "experiences": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (
                round(
                    successful * 100 / total,
                    2,
                )
                if total
                else 0.0
            ),
            "average_confidence": round(
                average_confidence,
                3,
            ),
            "average_quality": round(
                average_quality,
                2,
            ),
        }

    # -----------------------------------------------------

    def clear(
        self,
    ) -> None:

        self.experiences.clear()

        self.save()

    # -----------------------------------------------------

    def summary(
        self,
    ) -> dict:

        return {
            "repository": str(
                self.repository,
            ),
            "statistics": self.statistics(),
            "best_experiences": len(
                self.best(),
            ),
            "last_execution": (
                self.experiences[-1].to_dict() if self.experiences else None
            ),
        }
