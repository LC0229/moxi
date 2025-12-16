"""GitHub Trending crawler for fetching high-quality repositories."""

import time
from typing import List, Optional

import requests
from pydantic import BaseModel

from core import get_logger, settings
from core.errors import ImproperlyConfigured
from core.lib import extract_repo_owner_and_name, validate_github_url

logger = get_logger(__name__)


class RepositoryInfo(BaseModel):
    """Repository information for dataset generation."""

    url: str
    owner: str
    name: str
    stars: int
    language: Optional[str] = None
    has_readme: bool = False
    description: Optional[str] = None


class GithubTrendingCrawler:
    """Crawler for fetching high-quality GitHub repositories using GitHub API."""

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub Trending crawler.
        
        Args:
            github_token: GitHub personal access token. If None, uses settings.GITHUB_TOKEN.
                        Token is optional but recommended for higher rate limits.
        """
        self.token = github_token or settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
            logger.info("GitHub API authenticated", has_token=True)
        else:
            logger.warning("No GitHub token provided, rate limit: 60 requests/hour")
            logger.warning("With token: 5000 requests/hour. Consider setting GITHUB_TOKEN in .env")

    def _make_request(self, url: str, params: Optional[dict] = None) -> dict:
        """
        Make a GitHub API request with rate limit handling.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            ImproperlyConfigured: If API request fails
        """
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Check rate limit
            remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            if remaining < 10:
                logger.warning("GitHub API rate limit low", remaining=remaining)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error("GitHub API request failed", url=url, error=str(e))
            raise ImproperlyConfigured(f"GitHub API request failed: {str(e)}")

    def search_repositories(
        self,
        min_stars: int = 100,
        language: Optional[str] = None,
        limit: int = 100,
        sort: str = "stars",
        order: str = "desc"
    ) -> List[RepositoryInfo]:
        """
        Search GitHub repositories by criteria.
        
        Args:
            min_stars: Minimum number of stars
            language: Programming language filter (e.g., "Python", "JavaScript")
            limit: Maximum number of repositories to return
            sort: Sort by "stars", "forks", "updated", etc.
            order: "asc" or "desc"
            
        Returns:
            List of RepositoryInfo objects
        """
        query_parts = [f"stars:>={min_stars}"]
        if language:
            query_parts.append(f"language:{language}")
        
        query = " ".join(query_parts)
        logger.info("Searching GitHub repositories", 
                   query=query, min_stars=min_stars, limit=limit)
        
        repos: List[RepositoryInfo] = []
        page = 1
        per_page = min(100, limit)  # GitHub API max is 100 per page
        
        while len(repos) < limit:
            params = {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": per_page,
                "page": page
            }
            
            url = f"{self.base_url}/search/repositories"
            data = self._make_request(url, params=params)
            
            items = data.get("items", [])
            if not items:
                logger.info("No more repositories found", page=page)
                break
            
            for item in items:
                if len(repos) >= limit:
                    break
                
                repo_info = RepositoryInfo(
                    url=item["html_url"],
                    owner=item["owner"]["login"],
                    name=item["name"],
                    stars=item["stargazers_count"],
                    language=item.get("language"),
                    has_readme=item.get("has_readme", False),
                    description=item.get("description")
                )
                repos.append(repo_info)
            
            logger.info("Fetched repositories", 
                       current=len(repos), 
                       target=limit, 
                       page=page)
            
            # Rate limit: 30 requests per minute for authenticated, 10 for unauthenticated
            time.sleep(2 if self.token else 6)
            page += 1
        
        logger.info("Repository search complete", total=len(repos))
        return repos[:limit]

    def fetch_quality_repos(
        self,
        min_stars: Optional[int] = None,
        limit: int = 100,
        languages: Optional[List[str]] = None
    ) -> List[RepositoryInfo]:
        """
        Fetch quality repositories for training dataset.
        
        Args:
            min_stars: Minimum stars (defaults to settings.MIN_REPO_STARS)
            limit: Maximum number of repos (defaults to settings.MAX_REPOS_TO_CRAWL)
            languages: List of languages to filter (e.g., ["Python", "JavaScript"])
            
        Returns:
            List of RepositoryInfo objects
        """
        min_stars = min_stars or settings.MIN_REPO_STARS
        limit = min(limit, settings.MAX_REPOS_TO_CRAWL)
        
        all_repos: List[RepositoryInfo] = []
        
        if languages:
            # Search for each language separately
            repos_per_language = limit // len(languages)
            for language in languages:
                logger.info("Fetching repositories", language=language, limit=repos_per_language)
                repos = self.search_repositories(
                    min_stars=min_stars,
                    language=language,
                    limit=repos_per_language
                )
                all_repos.extend(repos)
        else:
            # Search all languages
            all_repos = self.search_repositories(
                min_stars=min_stars,
                limit=limit
            )
        
        # Filter repos with README
        repos_with_readme = [r for r in all_repos if r.has_readme]
        logger.info("Filtered repositories with README", 
                   total=len(all_repos), 
                   with_readme=len(repos_with_readme))
        
        return repos_with_readme[:limit]

