"""Analyze key files inside a repository."""

from pathlib import Path
from typing import Dict, Iterable

KEY_FILE_CANDIDATES = [
    "README.md",
    "readme.md",
    "README.rst",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "environment.yml",
    "main.py",
    "app.py",
    "manage.py",
]


def find_key_files(repo_path: Path, files: Iterable[Path]) -> Dict[str, Path]:
    """
    Find key files from a list of repository files.

    Args:
        repo_path: Root path of repository.
        files: Iterable of relative file paths.

    Returns:
        A mapping from logical name to absolute Path.
    """
    key_files: Dict[str, Path] = {}

    lower_map = {f.name.lower(): f for f in files}
    for candidate in KEY_FILE_CANDIDATES:
        name_lower = candidate.lower()
        if name_lower in lower_map:
            key_files[candidate] = repo_path / lower_map[name_lower]

    # Heuristic: first package __init__.py
    for f in files:
        parts = f.parts
        if len(parts) >= 2 and parts[-1] == "__init__.py":
            key_files.setdefault("package_init", repo_path / f)
            break

    return key_files

