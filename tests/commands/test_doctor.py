"""Tests for the doctor command."""

from ai_architect.commands.doctor import run


def test_doctor_reports_healthy() -> None:
    """Doctor must report a healthy environment."""
    result = run()

    assert result["status"] == "healthy"
    assert "python" in result
    assert "platform" in result
