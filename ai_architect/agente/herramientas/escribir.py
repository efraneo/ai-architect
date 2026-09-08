# mypy: ignore-errors
# Portado de OpenJarvis (https://github.com/openjarvis) — Apache License 2.0.
# Copyright de los autores de OpenJarvis. Archivo modificado para AI-architect
# (8 sep 2026): imports reescritos y acoplamientos a Rust/config sustituidos por piezas propias.
# La licencia completa está en ai_architect/agente/LICENCIA-OpenJarvis.txt.

"""File write tool — write content to files with path validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.agente.herramientas_base import BaseTool, ToolSpec
from ai_architect.agente.registro import ToolRegistry
from ai_architect.agente.tipos import ToolResult

# Maximum file size to write (10 MB)
_MAX_SIZE_BYTES = 10_485_760


@ToolRegistry.register("file_write")
class FileWriteTool(BaseTool):
    """Write content to files with optional directory restrictions."""

    tool_id = "file_write"

    def __init__(
        self,
        allowed_dirs: list[str] | None = None,
    ) -> None:
        self._allowed_dirs = [Path(d).resolve() for d in (allowed_dirs or [])]

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="file_write",
            description=("Write content to a file. Supports write and append modes."),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file.",
                    },
                    "mode": {
                        "type": "string",
                        "description": (
                            "Write mode: 'write' (overwrite/create)"
                            " or 'append' (append to existing)."
                            " Default: 'write'."
                        ),
                    },
                    "create_dirs": {
                        "type": "boolean",
                        "description": (
                            "Create parent directories if they"
                            " don't exist. Default: false."
                        ),
                    },
                },
                "required": ["path", "content"],
            },
            category="filesystem",
            required_capabilities=["file:write"],
        )

    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        if not self._allowed_dirs:
            return True
        resolved = path.resolve()
        return any(
            resolved == d or resolved.is_relative_to(d) for d in self._allowed_dirs
        )

    def execute(self, **params: Any) -> ToolResult:
        file_path = params.get("path", "")
        if not file_path:
            return ToolResult(
                tool_name="file_write",
                content="No path provided.",
                success=False,
            )

        content = params.get("content")
        if content is None:
            return ToolResult(
                tool_name="file_write",
                content="No content provided.",
                success=False,
            )

        mode = params.get("mode", "write")
        if mode not in ("write", "append"):
            return ToolResult(
                tool_name="file_write",
                content=f"Invalid mode: {mode!r}. Use 'write' or 'append'.",
                success=False,
            )

        create_dirs = params.get("create_dirs", False)

        path = Path(file_path)

        # Block sensitive files (secrets, credentials, keys)
        from ai_architect.agente.politica_archivos import is_sensitive_file

        if is_sensitive_file(path):
            return ToolResult(
                tool_name="file_write",
                content=f"Access denied: {file_path} is a sensitive file.",
                success=False,
            )

        if not self._is_path_allowed(path):
            return ToolResult(
                tool_name="file_write",
                content=f"Access denied: {file_path} is outside allowed directories.",
                success=False,
            )

        # Check content size before writing
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > _MAX_SIZE_BYTES:
            return ToolResult(
                tool_name="file_write",
                content=(
                    f"Content too large: {len(content_bytes)} bytes"
                    f" (max {_MAX_SIZE_BYTES})."
                ),
                success=False,
            )

        # Create parent directories if requested
        if create_dirs:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return ToolResult(
                    tool_name="file_write",
                    content=f"Cannot create directories: {exc}",
                    success=False,
                )
        else:
            if not path.parent.exists():
                return ToolResult(
                    tool_name="file_write",
                    content=(
                        f"Parent directory does not exist: {path.parent}."
                        " Set create_dirs=true to create it."
                    ),
                    success=False,
                )

        if mode == "write":
            try:
                from ai_architect.agente.seguridad import get_rust_module

                _rust = get_rust_module()
                _rust.FileWriteTool().execute(str(path), content)
            except ImportError:
                try:
                    path.write_text(content, encoding="utf-8")
                except OSError as exc:
                    return ToolResult(
                        tool_name="file_write",
                        content=f"Write error: {exc}",
                        success=False,
                    )
            except Exception as exc:
                return ToolResult(
                    tool_name="file_write",
                    content=f"Write error: {exc}",
                    success=False,
                )
        else:
            # append mode — always Python
            try:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(content)
            except PermissionError as exc:
                return ToolResult(
                    tool_name="file_write",
                    content=f"Permission denied: {exc}",
                    success=False,
                )
            except OSError as exc:
                return ToolResult(
                    tool_name="file_write",
                    content=f"Write error: {exc}",
                    success=False,
                )

        # Get final file size
        try:
            size = path.stat().st_size
        except OSError:
            size = len(content_bytes)

        return ToolResult(
            tool_name="file_write",
            content=f"Successfully wrote to {file_path}",
            success=True,
            metadata={"path": str(path.resolve()), "size_bytes": size},
        )


__all__ = ["FileWriteTool"]
