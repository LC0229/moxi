"""Utility functions for dataset generation."""

from pathlib import Path
from typing import Optional

from core import get_logger
from repo_analyzer import RepositoryInfo

logger = get_logger(__name__)


def read_readme(repo_info: RepositoryInfo) -> Optional[str]:
    """
    Read README content from repository.
    
    Args:
        repo_info: Repository information
        
    Returns:
        README content as string, or None if not found
    """
    # Try different README file names
    readme_candidates = ["README.md", "readme.md", "README.rst", "README.txt"]
    
    for readme_name in readme_candidates:
        if readme_name in repo_info.key_files:
            readme_path = repo_info.key_files[readme_name]
            try:
                with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    logger.debug("Read README", 
                               file=readme_name, 
                               length=len(content))
                    return content
            except Exception as e:
                logger.warning("Failed to read README", 
                             file=readme_name, 
                             error=str(e))
                continue
    
    # Try to find README in root directory
    repo_path = repo_info.path
    for readme_name in readme_candidates:
        readme_path = repo_path / readme_name
        if readme_path.exists():
            try:
                with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    logger.debug("Found README in root", file=readme_name)
                    return content
            except Exception as e:
                logger.warning("Failed to read README from root", 
                             file=readme_name, 
                             error=str(e))
                continue
    
    logger.warning("No README found", repo=str(repo_path))
    return None

