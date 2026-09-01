"""
=========================================================
Git Models
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class GitBranch:
    name: str

    current: bool = False


@dataclass(slots=True)
class GitCommit:
    hash: str

    author: str

    message: str

    created_at: datetime


@dataclass(slots=True)
class GitStatus:
    branch: str

    modified: list[str]

    created: list[str]

    deleted: list[str]

    untracked: list[str]

    clean: bool
