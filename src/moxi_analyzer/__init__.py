"""
Re-export repo analysis from the canonical implementation (moxi_chunk.repo_analyzer).
Use: from moxi_analyzer import analyze_repository, RepositoryInfo, ProjectType, ProjectLanguage
"""

from moxi_chunk.repo_analyzer import (
    analyze_repository,
    ProjectLanguage,
    ProjectType,
    RepositoryInfo,
)

__all__ = ["analyze_repository", "RepositoryInfo", "ProjectType", "ProjectLanguage"]
