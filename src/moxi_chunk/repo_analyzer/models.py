"""Data models for repository analysis."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List


class ProjectType(str, Enum):
    """Supported project types."""

    LIBRARY = "library"
    APPLICATION = "application"
    CLI = "cli"
    UNKNOWN = "unknown"


class ProjectLanguage(str, Enum):
    """Supported project languages."""

    PYTHON = "python"
    NODEJS = "nodejs"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"


@dataclass
class RepositoryInfo:
    """Aggregated information about a repository."""

    path: Path
    project_type: ProjectType
    project_language: ProjectLanguage = ProjectLanguage.UNKNOWN
    key_files: Dict[str, Path] = field(default_factory=dict)
    all_files: List[Path] = field(default_factory=list)

