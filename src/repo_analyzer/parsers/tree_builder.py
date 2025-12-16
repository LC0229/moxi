"""Build a directory tree representation for a repository."""

from pathlib import Path
from typing import List


def list_files(repo_path: Path) -> List[Path]:
    """
    List all files (relative paths) under the repository.

    Args:
        repo_path: Root path of repository.

    Returns:
        A list of relative file paths.
    """
    files: List[Path] = []
    for path in repo_path.rglob("*"):
        if path.is_file():
            files.append(path.relative_to(repo_path))
    return files

