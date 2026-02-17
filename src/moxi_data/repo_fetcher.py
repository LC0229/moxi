"""Core utilities for dataset generation - simplified to only fetch repositories."""

from typing import List, Optional

from core import get_logger, settings
from moxi_data.crawlers import AwesomeListsCrawler, GithubTrendingCrawler
from moxi_data.crawlers.github_repo_crawler import RepositoryInfo as CrawlerRepoInfo

logger = get_logger(__name__)


def fetch_repositories(
    source: str = "github",
    min_stars: Optional[int] = None,
    limit: Optional[int] = None,
    languages: Optional[List[str]] = None,
    project_type: Optional[str] = "webapp",
) -> List[CrawlerRepoInfo]:
    """
    Fetch repositories from various sources.
    
    Args:
        source: Source type ("github", "awesome", or "both")
        min_stars: Minimum stars filter (default: 20, lowered for better real projects)
        limit: Maximum number of repos to fetch
        languages: List of programming languages to filter (defaults to ["Python"] if None)
        project_type: Type of project to search for:
            - "webapp": Web applications (not frameworks)
            - "fullstack": Full-stack projects
            - "api": API projects
            - None: General search
        
    Returns:
        List of RepositoryInfo objects from crawlers
    """
    # Default to Python only if no languages specified
    if languages is None:
        languages = ["Python"]
        logger.info("No languages specified, defaulting to Python only")
    
    # Lower default min_stars to get more real projects (not just popular frameworks)
    if min_stars is None:
        min_stars = 20  # Lower threshold for real projects
    
    repos: List[CrawlerRepoInfo] = []
    
    if source in ["github", "both"]:
        logger.info("Fetching from GitHub", 
                   languages=languages, 
                   project_type=project_type,
                   min_stars=min_stars)
        github_crawler = GithubTrendingCrawler()
        github_repos = github_crawler.fetch_quality_repos(
            min_stars=min_stars,
            limit=limit or settings.MAX_REPOS_TO_CRAWL,
            languages=languages,
            project_type=project_type
        )
        repos.extend(github_repos)
        logger.info("Fetched from GitHub", count=len(github_repos), languages=languages, project_type=project_type)
    
    if source in ["awesome", "both"]:
        logger.info("Fetching from Awesome Lists")
        awesome_crawler = AwesomeListsCrawler()
        
        # Multiple Awesome Lists for more diverse repositories
        awesome_list_urls = [
            "https://github.com/vinta/awesome-python",
            "https://github.com/avelino/awesome-go",  # Go projects (will be filtered by language)
            "https://github.com/rust-unofficial/awesome-rust",  # Rust projects (will be filtered)
            "https://github.com/sindresorhus/awesome-nodejs",  # Node.js projects (will be filtered)
        ]
        
        # Fetch from multiple lists
        awesome_urls = awesome_crawler.fetch_from_multiple_lists(
            awesome_list_urls,
            limit=limit or settings.MAX_REPOS_TO_CRAWL
        )
        awesome_repos = awesome_crawler.convert_to_repo_info(awesome_urls)
        repos.extend(awesome_repos)
        logger.info("Fetched from Awesome Lists", count=len(awesome_repos))
    
    return repos
