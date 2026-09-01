"""
Execution Pipeline

Institutional Patch Execution Pipeline.

Responsible for applying, validating, rolling back, and verifying
Git unified-diff patches.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from ai_architect.execution.pipeline_state import ExecutionPipelineStateMixin
from ai_architect.patch_generator.models import Patch


class ExecutionPipeline(ExecutionPipelineStateMixin):
    """Execute validated patches through Git."""

    def __init__(self) -> None:
        self.executed_files = 0
        self.failed_files = 0
        self.last_result: dict = {}

    def _git_apply(
        self,
        repository: Path,
        patch: Patch,
        *,
        check_only: bool = False,
        reverse: bool = False,
    ) -> dict:
        if not repository.exists():
            return self._error(
                f"Repository does not exist: {repository}",
            )

        if not repository.is_dir():
            return self._error(
                f"Repository is not a directory: {repository}",
            )

        if not patch.diff.strip():
            return self._error(
                "Patch contains no unified diff.",
            )

        git_check = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "rev-parse",
                "--show-toplevel",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if git_check.returncode != 0:
            return {
                "success": False,
                "message": "Target directory is not a Git repository.",
                "stdout": git_check.stdout,
                "stderr": git_check.stderr,
                "returncode": git_check.returncode,
            }

        temporary_patch: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".patch",
                delete=False,
            ) as handle:
                handle.write(patch.diff)

                if not patch.diff.endswith("\n"):
                    handle.write("\n")

                temporary_patch = Path(handle.name)

            command = [
                "git",
                "-C",
                str(repository),
                "apply",
            ]

            if check_only:
                command.append("--check")

            if reverse:
                command.append("--reverse")

            command.append(str(temporary_patch))

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            success = result.returncode == 0

            if check_only and success:
                message = "Patch validation succeeded."
            elif success:
                message = "Patch applied successfully."
            else:
                message = "Git rejected the patch."

            return {
                "success": success,
                "message": message,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except FileNotFoundError:
            return {
                "success": False,
                "message": (
                    "Git executable was not found. "
                    "Install Git and ensure it is available on PATH."
                ),
                "stdout": "",
                "stderr": "",
                "returncode": 127,
            }

        except OSError as exc:
            return self._error(
                f"Git execution error: {exc}",
                stderr=str(exc),
            )

        finally:
            if temporary_patch is not None:
                try:
                    temporary_patch.unlink(missing_ok=True)
                except OSError:
                    pass

    @staticmethod
    def _error(
        message: str,
        *,
        stderr: str = "",
        returncode: int = 1,
    ) -> dict:
        return {
            "success": False,
            "message": message,
            "stdout": "",
            "stderr": stderr,
            "returncode": returncode,
        }

    def execute(
        self,
        repository: str | Path,
        patch: Patch,
    ) -> dict:
        """Validate and apply a patch atomically at the Git level."""

        repository = Path(repository).resolve()
        self.executed_files = 0
        self.failed_files = 0

        check = self._git_apply(
            repository,
            patch,
            check_only=True,
        )

        if not check["success"]:
            self.failed_files = patch.total_files

            result = {
                "success": False,
                "executed": 0,
                "failed": self.failed_files,
                "total": patch.total_files,
                "repository": str(repository),
                "message": check["message"],
                "stdout": check["stdout"],
                "stderr": check["stderr"],
                "returncode": check["returncode"],
            }

            self.last_result = result
            return result

        applied = self._git_apply(
            repository,
            patch,
        )

        if not applied["success"]:
            self.failed_files = patch.total_files

            result = {
                "success": False,
                "executed": 0,
                "failed": self.failed_files,
                "total": patch.total_files,
                "repository": str(repository),
                "message": applied["message"],
                "stdout": applied["stdout"],
                "stderr": applied["stderr"],
                "returncode": applied["returncode"],
            }

            self.last_result = result
            return result

        self.executed_files = patch.total_files

        result = {
            "success": True,
            "executed": self.executed_files,
            "failed": 0,
            "total": patch.total_files,
            "repository": str(repository),
            "message": applied["message"],
            "stdout": applied["stdout"],
            "stderr": applied["stderr"],
            "returncode": applied["returncode"],
        }

        self.last_result = result
        return result

    def dry_run(
        self,
        repository: str | Path,
        patch: Patch,
    ) -> dict:
        """Validate a patch without modifying the repository."""

        repository = Path(repository).resolve()
        self.executed_files = 0
        self.failed_files = 0

        result = self._git_apply(
            repository,
            patch,
            check_only=True,
        )

        self.last_result = {
            "success": bool(result["success"]),
            "approved": bool(result["success"]),
            "dry_run": True,
            "repository": str(repository),
            "files": patch.total_files,
            "message": result["message"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": result["returncode"],
        }

        if not result["success"]:
            self.failed_files = patch.total_files
            self.last_result["approved"] = False

        return self.last_result

    def rollback(
        self,
        repository: str | Path,
        patch: Patch,
    ) -> dict:
        """Validate and reverse a previously applied patch."""

        repository = Path(repository).resolve()

        check = self._git_apply(
            repository,
            patch,
            check_only=True,
            reverse=True,
        )

        if not check["success"]:
            return {
                "success": False,
                "repository": str(repository),
                "rolled_back": 0,
                "message": "Rollback validation failed.",
                "stdout": check["stdout"],
                "stderr": check["stderr"],
                "returncode": check["returncode"],
            }

        applied = self._git_apply(
            repository,
            patch,
            reverse=True,
        )

        if not applied["success"]:
            return {
                "success": False,
                "repository": str(repository),
                "rolled_back": 0,
                "message": "Rollback execution failed.",
                "stdout": applied["stdout"],
                "stderr": applied["stderr"],
                "returncode": applied["returncode"],
            }

        return {
            "success": True,
            "repository": str(repository),
            "rolled_back": patch.total_files,
            "message": "Patch rollback completed.",
            "stdout": applied["stdout"],
            "stderr": applied["stderr"],
            "returncode": applied["returncode"],
        }

    def verify(
        self,
        repository: str | Path,
    ) -> bool:
        """Verify that the target is an accessible Git repository."""

        repository = Path(repository).resolve()

        if not repository.exists() or not repository.is_dir():
            return False

        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "rev-parse",
                    "--show-toplevel",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except (FileNotFoundError, OSError):
            return False

        return result.returncode == 0
