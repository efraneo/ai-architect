"""
Pattern Miner

Execution Pattern Discovery Engine.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from ai_architect.memory.models import (
    Experience,
    ExperienceOutcome,
    LearningPattern,
)


class PatternMiner:
    """
    Discovers execution patterns from historical experiences.

    Responsibilities:
        • Success patterns
        • Failure patterns
        • Repository patterns
        • Provider patterns
        • Instruction patterns
        • Confidence trends
        • Risk trends
    """

    def mine(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        patterns: list[LearningPattern] = []

        patterns.extend(self.success_patterns(experiences))
        patterns.extend(self.failure_patterns(experiences))
        patterns.extend(self.provider_patterns(experiences))
        patterns.extend(self.repository_patterns(experiences))
        patterns.extend(self.keyword_patterns(experiences))

        return patterns

    def success_patterns(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        successful = [e for e in experiences if e.outcome == ExperienceOutcome.SUCCESS]

        return [
            LearningPattern(
                name="successful_executions",
                description="Successful executions.",
                confidence=1.0,
                occurrences=len(successful),
            )
        ]

    def failure_patterns(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        failed = [e for e in experiences if e.outcome == ExperienceOutcome.FAILURE]

        return [
            LearningPattern(
                name="failed_executions",
                description="Failed executions.",
                confidence=1.0,
                occurrences=len(failed),
            )
        ]

    def provider_patterns(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        grouped: defaultdict[str, list[Experience]] = defaultdict(list)

        for experience in experiences:
            grouped[experience.provider].append(experience)

        patterns: list[LearningPattern] = []

        for provider, items in grouped.items():
            success = sum(
                1
                for experience in items
                if experience.outcome == ExperienceOutcome.SUCCESS
            )

            confidence = success / len(items) if items else 0.0

            patterns.append(
                LearningPattern(
                    name=f"provider:{provider}",
                    description="Provider performance.",
                    confidence=round(confidence, 3),
                    occurrences=len(items),
                )
            )

        return patterns

    def repository_patterns(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        counter: Counter[str] = Counter(e.repository for e in experiences)

        return [
            LearningPattern(
                name=f"repository:{repo}",
                description="Repository activity.",
                confidence=1.0,
                occurrences=count,
            )
            for repo, count in counter.items()
        ]

    def keyword_patterns(
        self,
        experiences: list[Experience],
    ) -> list[LearningPattern]:
        counter: Counter[str] = Counter()

        for experience in experiences:
            counter.update(experience.instruction.lower().split())

        patterns: list[LearningPattern] = []

        for word, count in counter.most_common(25):
            patterns.append(
                LearningPattern(
                    name=f"keyword:{word}",
                    description="Frequent instruction keyword.",
                    confidence=1.0,
                    occurrences=count,
                )
            )

        return patterns
