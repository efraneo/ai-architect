"""
Project Memory

Persistent Project Knowledge
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast


class ProjectMemory:
    """
    Persistent project memory.

    Stores architectural knowledge, execution history,
    metrics and learned information between executions.
    """

    def __init__(
        self,
        storage: str = ".quant",
    ) -> None:
        self.root = Path(storage)

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.memory_file = self.root / "project_memory.json"

    def _default(self) -> dict[str, Any]:
        return {
            "created": datetime.utcnow().isoformat(),
            "projects": {},
        }

    def load(
        self,
    ) -> dict[str, Any]:
        if not self.memory_file.exists():
            return self._default()

        try:
            data = json.loads(
                self.memory_file.read_text(
                    encoding="utf-8",
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return self._default()

        if not isinstance(
            data,
            dict,
        ):
            return self._default()

        return cast(
            dict[str, Any],
            data,
        )

    def save(
        self,
        knowledge: dict[str, Any],
    ) -> None:
        data = self.load()

        data["knowledge"] = dict(
            knowledge,
        )

        data["updated"] = datetime.utcnow().isoformat()

        self.memory_file.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def update_project(
        self,
        project: str,
        information: dict[str, Any],
    ) -> None:
        data = self.load()

        projects = data.get(
            "projects",
        )

        if not isinstance(
            projects,
            dict,
        ):
            projects = {}
            data["projects"] = projects

        current = projects.get(
            project,
        )

        if not isinstance(
            current,
            dict,
        ):
            current = {}
            projects[project] = current

        current.update(
            information,
        )

        current["updated"] = datetime.utcnow().isoformat()

        data["updated"] = datetime.utcnow().isoformat()

        self.memory_file.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def project(
        self,
        project: str,
    ) -> dict[str, Any]:
        data = self.load()

        projects = data.get(
            "projects",
            {},
        )

        if not isinstance(
            projects,
            dict,
        ):
            return {}

        value = projects.get(
            project,
            {},
        )

        if not isinstance(
            value,
            dict,
        ):
            return {}

        return cast(
            dict[str, Any],
            value,
        )

    def knowledge(
        self,
    ) -> dict[str, Any]:
        value = self.load().get(
            "knowledge",
            {},
        )

        if not isinstance(
            value,
            dict,
        ):
            return {}

        return cast(
            dict[str, Any],
            value,
        )

    def clear(self) -> None:
        if self.memory_file.exists():
            self.memory_file.unlink()

    def statistics(
        self,
    ) -> dict[str, Any]:
        data = self.load()

        projects = data.get(
            "projects",
            {},
        )

        project_count = (
            len(projects)
            if isinstance(
                projects,
                dict,
            )
            else 0
        )

        return {
            "projects": project_count,
            "has_knowledge": ("knowledge" in data),
            "updated": data.get(
                "updated",
            ),
        }
