"""Detect project type from repository files."""

from pathlib import Path
from typing import Iterable

from repo_analyzer.models import ProjectType


def detect_project_type(files: Iterable[Path]) -> ProjectType:
    """
    Heuristic detection of project type based on file names.

    Args:
        files: Iterable of relative file paths.

    Returns:
        ProjectType enum value.
    """
    names = {f.name.lower() for f in files}
    paths = {"/".join(f.parts).lower() for f in files}

    # Library indicators (check first - strongest signal)
    # Libraries almost always have setup.py or pyproject.toml
    if "pyproject.toml" in names or "setup.py" in names or "setup.cfg" in names:
        return ProjectType.LIBRARY

    # CLI indicators
    cli_signals = {"cli.py", "cli"}
    if names & cli_signals or any("command" in p and p.endswith(".py") for p in paths):
        return ProjectType.CLI

    # Application indicators
    # Note: main.py can exist in libraries (e.g., test scripts), so check last
    app_signals = {"main.py", "app.py", "manage.py"}
    if names & app_signals:
        return ProjectType.APPLICATION

    return ProjectType.UNKNOWN

