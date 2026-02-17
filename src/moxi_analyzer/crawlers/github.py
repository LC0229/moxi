"""GitHub repository crawler for cloning repositories."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from core import get_logger
from core.errors import RepositoryNotFound
from core.lib import ensure_dir_exists, extract_repo_owner_and_name, validate_github_url

logger = get_logger(__name__)


class GithubCrawler:
    """Crawler for fetching GitHub repositories."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize GitHub crawler.
        
        Args:
            cache_dir: Directory to cache cloned repositories. 
                      If None, uses temporary directory.
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
            ensure_dir_exists(self.cache_dir)
        else:
            self.cache_dir = None

    def fetch(self, repo_url: str, use_cache: bool = True) -> Path:
        """
        Fetch a GitHub repository by cloning it.
        
        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
            use_cache: If True and cache_dir is set, reuse cached repos
            
        Returns:
            Path to the cloned repository
            
        Raises:
            RepositoryNotFound: If the repository cannot be cloned
        """
        if not validate_github_url(repo_url):
            raise RepositoryNotFound(f"Invalid GitHub URL: {repo_url}")

        owner, repo_name = extract_repo_owner_and_name(repo_url)
        logger.info("Fetching repository", url=repo_url, owner=owner, repo=repo_name)

        # If using cache, check if repo already exists
        if use_cache and self.cache_dir:
            cached_path = self.cache_dir / owner / repo_name
            if cached_path.exists():
                logger.info("Using cached repository", path=str(cached_path))
                return cached_path

        # Clone to temporary or cache directory
        if self.cache_dir and use_cache:
            target_dir = self.cache_dir / owner
            ensure_dir_exists(target_dir)
            repo_path = target_dir / repo_name
            temp_dir = None
        else:
            temp_dir = tempfile.mkdtemp(prefix="moxi_")
            repo_path = Path(temp_dir) / repo_name

        try:
            # Clone the repository
            logger.info("Cloning repository", url=repo_url, target=str(repo_path))
            result = subprocess.run(
                ["git", "clone", repo_url, str(repo_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error("Failed to clone repository", url=repo_url, error=error_msg)
                raise RepositoryNotFound(f"Failed to clone {repo_url}: {error_msg}")

            logger.info("Repository cloned successfully", path=str(repo_path))
            return repo_path

        except subprocess.TimeoutExpired:
            logger.error("Clone timeout", url=repo_url)
            raise RepositoryNotFound(f"Timeout cloning {repo_url}")
        except Exception as e:
            logger.error("Unexpected error cloning repository", url=repo_url, error=str(e))
            # Clean up on error
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise RepositoryNotFound(f"Error cloning {repo_url}: {str(e)}")

