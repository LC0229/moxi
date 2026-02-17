"""Local repository crawler for handling local file paths."""

from pathlib import Path
from typing import Optional

from core import get_logger
from core.errors import RepositoryNotFound
from core.lib import ensure_dir_exists

logger = get_logger(__name__)


class LocalCrawler:
    """Crawler for handling local repository paths."""

    def fetch(self, repo_path: str) -> Path:
        """
        Validate and return a local repository path.
        
        Args:
            repo_path: Local file system path to repository
            
        Returns:
            Path object pointing to the repository
            
        Raises:
            RepositoryNotFound: If the path doesn't exist or isn't a directory
        """
        path = Path(repo_path).expanduser().resolve()

        if not path.exists():
            raise RepositoryNotFound(f"Path does not exist: {repo_path}")

        if not path.is_dir():
            raise RepositoryNotFound(f"Path is not a directory: {repo_path}")

        # Check if it looks like a git repository
        if not (path / ".git").exists():
            logger.warning("Path does not appear to be a git repository", path=str(path))

        logger.info("Using local repository", path=str(path))
        return path

