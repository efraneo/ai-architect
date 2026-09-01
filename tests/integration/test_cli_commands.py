from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_architect import cli


def test_cli_analyze_json_returns_success(tmp_path: Path, monkeypatch, capsys) -> None:
    (tmp_path / "sample.py").write_text(
        "def hello():\n    return 'world'\n", encoding="utf-8"
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["ai-architect", "analyze", str(tmp_path), "--json"],
    )

    cli.main()

    output = capsys.readouterr().out
    payload = json.loads(output)

    assert payload["success"] is True
    assert payload["repository"] == str(tmp_path.resolve())


def test_cli_review_json_exports_report(tmp_path: Path, monkeypatch, capsys) -> None:
    (tmp_path / "sample.py").write_text(
        "def hello():\n    return 'world'\n", encoding="utf-8"
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["ai-architect", "review", str(tmp_path), "--json"],
    )

    cli.main()

    output = capsys.readouterr().out
    payload = json.loads(output)

    assert payload["success"] is True
    assert "score" in payload
    assert (tmp_path / ".ai_architect" / "review.json").exists()
    assert (tmp_path / ".ai_architect" / "review.md").exists()
