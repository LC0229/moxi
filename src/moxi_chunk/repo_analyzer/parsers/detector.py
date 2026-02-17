"""Detect project type and language from repository files."""

from pathlib import Path
from typing import Iterable

from moxi_chunk.repo_analyzer.models import ProjectLanguage, ProjectType


def detect_project_type(files: Iterable[Path]) -> ProjectType:
    """
    Heuristic detection of project type based on file names and structure.

    Args:
        files: Iterable of relative file paths.

    Returns:
        ProjectType enum value.
    """
    names = {f.name.lower() for f in files}
    paths = {"/".join(f.parts).lower() for f in files}
    
    # Count Python files to help determine project type
    py_files = [f for f in files if f.suffix == ".py"]
    py_file_count = len(py_files)

    # IMPORTANT: Check APPLICATION indicators FIRST (before library check)
    # Many modern applications use pyproject.toml, but they're still applications
    # if they have entry points like main.py, app.py, etc.
    
    # Application indicators (check FIRST - strongest signal for applications)
    app_signals = {
        "main.py",
        "app.py",
        "manage.py",  # Django
        "wsgi.py",  # WSGI apps
        "asgi.py",  # ASGI apps
        "application.py",
        "server.py",
    }
    if any(signal in names for signal in app_signals):
        return ProjectType.APPLICATION
    
    # Check for web framework indicators (also strong signal for applications)
    web_frameworks = ["flask", "django", "fastapi", "tornado", "bottle"]
    if any(framework in p for p in paths for framework in web_frameworks):
        return ProjectType.APPLICATION
    
    # Check for Docker/containerization (indicates runnable application)
    if "docker-compose.yml" in names or "dockerfile" in names:
        # If has Docker + pyproject.toml, likely an application
        return ProjectType.APPLICATION

    # CLI indicators (check before library)
    cli_signals = {
        "cli.py",
        "cli",
        "command.py",
        "commands.py",
        "__main__.py",  # Python -m style CLI
    }
    if any(signal in names for signal in cli_signals):
        return ProjectType.CLI
    
    # Check for click, argparse, or typer usage (CLI frameworks)
    cli_paths = ["cli/", "commands/", "cmd/"]
    if any(cli_path in p for p in paths for cli_path in cli_paths):
        return ProjectType.CLI

    # NOW check for library indicators (only if no application/CLI signals found)
    # Libraries almost always have setup.py or pyproject.toml
    library_indicators = {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "poetry.lock",  # Poetry projects are usually libraries
    }
    if any(indicator in names for indicator in library_indicators):
        return ProjectType.LIBRARY
    
    # Check for src/ or package structure (common in libraries)
    if any("src/" in p or "/__init__.py" in p for p in paths):
        if py_file_count > 3:  # Multiple Python files suggest library
            return ProjectType.LIBRARY

    # If we have many Python files but no clear indicator, default to library
    if py_file_count > 5:
        return ProjectType.LIBRARY

    return ProjectType.UNKNOWN


def detect_project_language(files: Iterable[Path]) -> ProjectLanguage:
    """
    Detect project language based on characteristic files.

    Args:
        files: Iterable of relative file paths.

    Returns:
        ProjectLanguage enum value.
    """
    names = {f.name.lower() for f in files}

    # Python indicators
    python_indicators = {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "Pipfile",
        "poetry.lock",
    }
    if any(indicator in names for indicator in python_indicators):
        return ProjectLanguage.PYTHON

    # Check for .py files (fallback for Python)
    if any(f.suffix == ".py" for f in files):
        return ProjectLanguage.PYTHON

    # Node.js/JavaScript indicators
    nodejs_indicators = {
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
    }
    if any(indicator in names for indicator in nodejs_indicators):
        return ProjectLanguage.NODEJS

    # Go indicators
    go_indicators = {"go.mod", "go.sum", "Gopkg.toml", "Gopkg.lock"}
    if any(indicator in names for indicator in go_indicators):
        return ProjectLanguage.GO

    # Rust indicators
    rust_indicators = {"Cargo.toml", "Cargo.lock"}
    if any(indicator in names for indicator in rust_indicators):
        return ProjectLanguage.RUST

    return ProjectLanguage.UNKNOWN

