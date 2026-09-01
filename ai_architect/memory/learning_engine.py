"""
Learning Engine

Continuous Learning System.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from ai_architect.memory.models import (
    Experience,
    ExperienceOutcome,
    LearningPattern,
    MemorySnapshot,
)


class LearningEngine:
    """
    Learns from previous executions.

    This class never stores data.
    It only transforms experiences into knowledge.
    """

    def learn(
        self,
        snapshot: MemorySnapshot,
    ) -> list[LearningPattern]:
        patterns: list[LearningPattern] = []

        patterns.extend(self._provider_patterns(snapshot.experiences))
        patterns.extend(self._repository_patterns(snapshot.experiences))
        patterns.extend(self._confidence_patterns(snapshot.experiences))
        patterns.extend(self._risk_patterns(snapshot.experiences))
        patterns.extend(self._instruction_patterns(snapshot.experiences))

        return patterns

    def success_rate(
        self,
        experiences: list[Experience],
    ) -> float:
        if not experiences:
            return 0.0

        success = sum(
            1
            for experience in experiences
            if experience.outcome == ExperienceOutcome.SUCCESS
        )

        return round(
            success * 100 / len(experiences),
            2,
        )

    def provider_statistics(
        self,
        experiences: list[Experience],
    ) -> dict[str, dict[str, Any]]:
        result: defaultdict[str, list[Experience]] = defaultdict(list)

        for experience in experiences:
            result[experience.provider].append(experience)

        report: dict[str, dict[str, Any]] = {}

        for provider, items in result.items():
            report[provider] = {
                "executions": len(items),
                "success_rate": self.success_rate(items),
                "average_confidence": round(
                    sum(experience.confidence for experience in items) / len(items),
                    3,
                ),
            }

        return report

    def recommendations(
        self,
        snapshot: MemorySnapshot,
    ) -> list[str]:
        recommendations: list[str] = []

        stats = self.provider_statistics(
            snapshot.experiences,
        )

        if stats:
            best = max(
                stats.items(),
                key=lambda item: item[1]["success_rate"],
            )

            recommendations.append(
                f"Prefer provider {best[0]} ({best[1]['success_rate']}% success)."
            )

        if self.success_rate(snapshot.experiences) < 60:
            recommendations.append("Repository requires additional learning.")

        return recommendations

    def _provider_patterns(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        patterns: list[LearningPattern] = []

        stats = self.provider_statistics(experiences)

        for provider, data in stats.items():
            patterns.append(
                LearningPattern(
                    name=f"provider:{provider}",
                    description=(f"{provider} success {data['success_rate']}%"),
                    confidence=float(data["average_confidence"]),
                    occurrences=int(data["executions"]),
                )
            )

        return patterns

    def _repository_patterns(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        counter: Counter[str] = Counter(e.repository for e in experiences)

        return [
            LearningPattern(
                name=f"repository:{repo}",
                description="Repository activity",
                confidence=1.0,
                occurrences=count,
            )
            for repo, count in counter.items()
        ]

    def _confidence_patterns(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        if not experiences:
            return []

        average = sum(experience.confidence for experience in experiences) / len(
            experiences
        )

        return [
            LearningPattern(
                name="confidence",
                description="Average confidence",
                confidence=round(average, 3),
                occurrences=len(experiences),
            )
        ]

    def _risk_patterns(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        if not experiences:
            return []

        average = sum(experience.risk for experience in experiences) / len(experiences)

        return [
            LearningPattern(
                name="risk",
                description="Average execution risk",
                confidence=max(0.0, 1 - average),
                occurrences=len(experiences),
            )
        ]

    def _instruction_patterns(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        counter: Counter[str] = Counter()

        for experience in experiences:
            words = experience.instruction.lower().split()
            counter.update(words)

        return [
            LearningPattern(
                name=f"keyword:{word}",
                description="Frequent instruction keyword",
                confidence=1.0,
                occurrences=count,
            )
            for word, count in counter.most_common(15)
        ]
