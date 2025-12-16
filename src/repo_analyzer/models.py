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


@dataclass
class RepositoryInfo:
    """Aggregated information about a repository."""

    path: Path
    project_type: ProjectType
    key_files: Dict[str, Path] = field(default_factory=dict)
    all_files: List[Path] = field(default_factory=list)

