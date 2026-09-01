"""Regression tests for ``ReviewEngine.statistics()``.

``ReviewEngine`` used to shadow ``ReviewStateMixin.statistics()`` with a
staticmethod that *required* a ``report`` argument. ``Reviewer.statistics()``
called it with no arguments, so it raised ``TypeError`` at runtime. No test
covered that path, so the break went unnoticed.

Both forms are legitimate and in use:

* with a report — ``commands/review.py`` and ``ReviewEngine.to_dict``
* without one   — ``Reviewer.statistics``, which wants the last review

So ``report`` is optional, and these tests pin that contract down.
"""

from __future__ import annotations

import inspect
from pathlib import Path

from ai_architect.reviewer.review_engine import ReviewEngine
from ai_architect.reviewer.reviewer import Reviewer

CLAVES_ESPERADAS = {
    "reviewed",
    "score",
    "approved",
    "total",
    "critical",
    "errors",
    "warnings",
    "info",
}


def test_reviewer_statistics_no_requiere_argumentos() -> None:
    """The bug: this call used to raise TypeError."""
    stats = Reviewer().statistics()

    assert isinstance(stats, dict)


def test_reviewer_statistics_incluye_las_claves_del_mixin() -> None:
    stats = Reviewer().statistics()

    assert CLAVES_ESPERADAS.issubset(stats)


def test_reviewer_statistics_agrega_la_aprobacion() -> None:
    stats = Reviewer().statistics()

    assert "approval" in stats


def test_engine_statistics_sin_informe_devuelve_ceros() -> None:
    """Without a previous review there is no report, and it must not explode."""
    stats = ReviewEngine().statistics()

    assert stats["score"] == 0.0
    assert stats["approved"] is False
    assert stats["total"] == 0


def test_engine_statistics_acepta_informe_opcional() -> None:
    """Guards the regression: ``report`` must stay optional.

    Making it required again would break ``Reviewer.statistics()``.
    """
    parametros = inspect.signature(ReviewEngine.statistics).parameters

    assert list(parametros) == ["self", "report"]
    assert parametros["report"].default is None


def test_engine_statistics_con_informe_y_sin_el_coinciden(tmp_path: Path) -> None:
    """Both forms describe the same review, so the numbers must agree."""
    (tmp_path / "sample.py").write_text("value = 1\n", encoding="utf-8")

    engine = ReviewEngine()
    report = engine.review(tmp_path)

    assert engine.statistics(report) == engine.statistics()
