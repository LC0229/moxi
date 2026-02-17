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
            ImproperlyConfigured: If API request fails (except 422 which is handled by caller)
        """
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            # Handle 422 error (GitHub API limit: max 1000 results)
            if response.status_code == 422:
                error_data = response.json()
                error_message = error_data.get("message", "Unprocessable Entity")
                if "Only the first 1000 search results" in error_message:
                    # This is expected when reaching GitHub's 1000 result limit
                    raise requests.exceptions.HTTPError(
                        f"422: GitHub API limit reached (max 1000 results)",
                        response=response
                    )
            
            response.raise_for_status()
            
            # Check rate limit
            remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            if remaining < 10:
                logger.warning("GitHub API rate limit low", remaining=remaining)
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            # Re-raise 422 errors so caller can handle them gracefully
            if "422" in str(e) or response.status_code == 422:
                raise
            logger.error("GitHub API request failed", url=url, error=str(e))
            raise ImproperlyConfigured(f"GitHub API request failed: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error("GitHub API request failed", url=url, error=str(e))
            raise ImproperlyConfigured(f"GitHub API request failed: {str(e)}")

    def search_repositories(
        self,
        min_stars: int = 100,
        language: Optional[str] = None,
        limit: Optional[int] = None,
        sort: str = "stars",
        order: str = "desc",
        project_type: Optional[str] = None
    ) -> List[RepositoryInfo]:
        """
        Search GitHub repositories by criteria.
        
        Args:
            min_stars: Minimum number of stars
            language: Programming language filter (e.g., "Python", "JavaScript")
            limit: Maximum number of repositories to return
            sort: Sort by "stars", "forks", "updated", etc.
            order: "asc" or "desc"
            project_type: Type of project to search for ("webapp", "fullstack", "api", None for general)
            
        Returns:
            List of RepositoryInfo objects
        """
        query_parts = [f"stars:>={min_stars}"]
        
        # Add project type specific queries (for real applications, not frameworks)
        # Use simpler queries that are more likely to return results
        if project_type == "webapp":
            # Search for web applications - use broader terms
            query_parts.append("(webapp OR \"web app\" OR \"web application\" OR \"full stack\" OR fullstack)")
            query_parts.append("-framework -library -boilerplate -template -starter")
        elif project_type == "fullstack":
            # Search for full-stack projects
            query_parts.append("(\"full stack\" OR fullstack OR \"frontend backend\" OR \"api server\")")
            query_parts.append("-framework -library -boilerplate")
        elif project_type == "api":
            # Search for API projects
            query_parts.append("(api OR \"rest api\" OR \"graphql api\" OR \"api server\")")
            query_parts.append("-framework -library -sdk -boilerplate")
        
        # Always exclude frameworks and libraries (but less aggressively)
        if not project_type:
            query_parts.append("-framework -library -boilerplate -template")
        
        # Exclude old/complex projects (but make it optional if no results)
        # Don't exclude Java - some good projects use Java
        # Use more recent date to get more results
        query_parts.append("pushed:>2022-01-01")  # Last 3 years (more lenient)
        
        if language:
            # GitHub API requires lowercase language names
            # "Python" -> "python", "JavaScript" -> "javascript", etc.
            language_lower = language.lower()
            query_parts.append(f"language:{language_lower}")
        
        query = " ".join(query_parts)
        # Default limit if not provided
        if limit is None:
            limit = settings.MAX_REPOS_TO_CRAWL
        logger.info("Searching GitHub repositories", 
                   query=query, min_stars=min_stars, limit=limit)
        
        repos: List[RepositoryInfo] = []
        page = 1
        per_page = min(100, limit)  # GitHub API max is 100 per page
        max_pages = 10  # GitHub API search limit: max 1000 results (10 pages × 100 per page)
        
        while len(repos) < limit and page <= max_pages:
            params = {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": per_page,
                "page": page
            }
            
            url = f"{self.base_url}/search/repositories"
            try:
                data = self._make_request(url, params=params)
            except Exception as e:
                # Handle 422 error (GitHub API limit: max 1000 results)
                if "422" in str(e) or "Unprocessable Entity" in str(e):
                    logger.warning("GitHub API limit reached (max 1000 results)", 
                                 page=page, 
                                 repos_fetched=len(repos),
                                 hint="GitHub API only returns max 1000 results per search query")
                    break
                else:
                    raise  # Re-raise other errors
            
            items = data.get("items", [])
            if not items:
                logger.info("No more repositories found", page=page)
                break
            
            for item in items:
                    if len(repos) >= limit:
                        break
                    
                    # Additional language filter: GitHub API's language field may not match query
                    repo_language = item.get("language", "").lower() if item.get("language") else ""
                    if language:
                        language_lower = language.lower()
                        # Skip if language doesn't match (GitHub API sometimes returns wrong language)
                        if repo_language and repo_language != language_lower:
                            logger.debug("Skipping repo with mismatched language",
                                       repo=item["name"],
                                       expected=language_lower,
                                       actual=repo_language)
                            continue
                    
                    # Filter: Exclude content list projects based on description and topics
                    description = (item.get("description") or "").lower()
                    topics = item.get("topics", [])
                    repo_name = item["name"].lower()
                    
                    exclude_keywords = [
                        "awesome", "list", "books", "resources", "curated",
                        "collection", "learning", "tutorial", "course", "education",
                        "framework", "library", "boilerplate", "template", "starter",
                        "sdk", "toolkit", "engine", "compiler", "interpreter"
                    ]
                    
                    # Skip if description contains exclude keywords
                    if any(keyword in description for keyword in exclude_keywords):
                        logger.debug("Skipping excluded project (description)",
                                   repo=item["name"],
                                   description=description[:100])
                        continue
                    
                    # Skip if topics contain exclude keywords
                    if any(topic.lower() in exclude_keywords for topic in topics):
                        logger.debug("Skipping excluded project (topics)",
                                   repo=item["name"],
                                   topics=topics)
                        continue
                    
                    # Skip if repository name contains exclude keywords
                    exclude_name_keywords = ["awesome", "list", "framework", "library", "sdk", "toolkit"]
                    if any(keyword in repo_name for keyword in exclude_name_keywords):
                        logger.debug("Skipping excluded project (name)",
                                   repo=item["name"])
                        continue
                    
                    # Skip very old projects (likely too complex/legacy)
                    # Check if last updated is too old (more than 2 years)
                    updated_at = item.get("updated_at", "")
                    if updated_at:
                        from datetime import datetime
                        try:
                            update_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            two_years_ago = datetime.now().replace(year=datetime.now().year - 2)
                            if update_date < two_years_ago:
                                logger.debug("Skipping old project",
                                           repo=item["name"],
                                           updated=updated_at)
                                continue
                        except:
                            pass
                    
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
        
        logger.info("Repository search complete", total=len(repos), query=query)
        
        # If no results and we used a strict query, try a simpler fallback
        if len(repos) == 0 and project_type:
            logger.warning("No results with strict query, trying simpler fallback", 
                         original_query=query, project_type=project_type)
            # Fallback: simpler query without project_type restrictions
            fallback_query_parts = [f"stars:>={min_stars}"]
            if language:
                language_lower = language.lower()
                fallback_query_parts.append(f"language:{language_lower}")
            fallback_query_parts.append("-framework -library -boilerplate")
            fallback_query_parts.append("pushed:>2022-01-01")
            
            fallback_query = " ".join(fallback_query_parts)
            logger.info("Trying fallback query", query=fallback_query)
            
            # Try one page with fallback
            try:
                params = {
                    "q": fallback_query,
                    "sort": "updated",
                    "order": "desc",
                    "per_page": min(100, limit),
                    "page": 1
                }
                url = f"{self.base_url}/search/repositories"
                data = self._make_request(url, params=params)
                items = data.get("items", [])
                
                for item in items[:limit]:
                    # Apply same filters as before
                    description = (item.get("description") or "").lower()
                    topics = item.get("topics", [])
                    repo_name = item["name"].lower()
                    
                    exclude_keywords = [
                        "awesome", "list", "framework", "library", "boilerplate", 
                        "template", "starter", "sdk", "toolkit"
                    ]
                    
                    if any(keyword in description for keyword in exclude_keywords):
                        continue
                    if any(topic.lower() in exclude_keywords for topic in topics):
                        continue
                    if any(keyword in repo_name for keyword in ["awesome", "list", "framework", "library"]):
                        continue
                    
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
                
                logger.info("Fallback query returned results", count=len(repos))
            except Exception as e:
                logger.warning("Fallback query also failed", error=str(e))
        
        return repos[:limit]

    def fetch_quality_repos(
        self,
        min_stars: Optional[int] = None,
        limit: Optional[int] = None,
        languages: Optional[List[str]] = None,
        project_type: Optional[str] = None
    ) -> List[RepositoryInfo]:
        """
        Fetch quality repositories for training dataset.
        
        Args:
            min_stars: Minimum stars (defaults to settings.MIN_REPO_STARS, lowered for better results)
            limit: Maximum number of repos (defaults to settings.MAX_REPOS_TO_CRAWL)
            languages: List of languages to filter (e.g., ["Python", "JavaScript"])
            project_type: Type of project ("webapp", "fullstack", "api", None for general)
            
        Returns:
            List of RepositoryInfo objects
        """
        min_stars = min_stars or settings.MIN_REPO_STARS
        limit = limit or settings.MAX_REPOS_TO_CRAWL  # Use settings default if not provided
        limit = min(limit, settings.MAX_REPOS_TO_CRAWL)  # But don't exceed max
        
        all_repos: List[RepositoryInfo] = []
        
        if languages:
            # Search for each language separately
            repos_per_language = limit // len(languages)
            for language in languages:
                logger.info("Fetching repositories", language=language, limit=repos_per_language, project_type=project_type)
                repos = self.search_repositories(
                    min_stars=min_stars,
                    language=language,
                    limit=repos_per_language,
                    project_type=project_type
                )
                all_repos.extend(repos)
        else:
            # Search all languages
            all_repos = self.search_repositories(
                min_stars=min_stars,
                limit=limit,
                project_type=project_type
            )
        
        # Note: We don't filter by has_readme here because:
        # 1. GitHub API's has_readme field may be inaccurate
        # 2. We'll check for README when we actually clone and analyze the repo
        # 3. This allows us to fetch more repos and filter later if needed
        logger.info("Fetched repositories", 
                   total=len(all_repos))
        
        return all_repos[:limit]

