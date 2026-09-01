"""
=========================================================
Filesystem Constants
=========================================================
"""

from pathlib import Path

MODULE_ID = "filesystem"

MODULE_NAME = "Filesystem"

MODULE_VERSION = "1.0.0"

DEFAULT_ALLOWED_EXTENSIONS = {
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".md",
    ".txt",
}

DEFAULT_IGNORED_DIRECTORIES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    "node_modules",
}

DEFAULT_IGNORED_FILES = {
    ".DS_Store",
    "Thumbs.db",
}

ROOT_MARKERS = (
    "pyproject.toml",
    "requirements.txt",
    ".git",
)


def is_root(path: Path) -> bool:
    """
    Detecta si una carpeta parece ser
    la raíz de un proyecto.
    """
    return any((path / marker).exists() for marker in ROOT_MARKERS)
