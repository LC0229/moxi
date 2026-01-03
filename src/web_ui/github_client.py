"""GitHub API client for fetching user repositories."""

from typing import List, Optional

import requests

from core import get_logger

logger = get_logger(__name__)


class GitHubClient:
    """GitHub API client for fetching repositories."""

    def __init__(self, token: str):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base_url = "https://api.github.com"

    def get_user_repos(self, username: Optional[str] = None) -> List[dict]:
        """
        Get all repositories for a user.
        
        Args:
            username: GitHub username (if None, uses authenticated user)
            
        Returns:
            List of repository dictionaries with:
            - name: Repository name
            - full_name: Full repository name (owner/repo)
            - html_url: Repository URL
            - description: Repository description
            - private: Whether repository is private
            - default_branch: Default branch name
        """
        try:
            if username:
                # Get repos for a specific user
                url = f"{self.base_url}/users/{username}/repos"
            else:
                # Get repos for authenticated user
                url = f"{self.base_url}/user/repos"
            
            repos = []
            page = 1
            per_page = 100
            
            while True:
                params = {
                    "page": page,
                    "per_page": per_page,
                    "sort": "updated",
                    "direction": "desc",
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code != 200:
                    logger.error("Failed to fetch repositories",
                               status_code=response.status_code,
                               response=response.text)
                    break
                
                page_repos = response.json()
                if not page_repos:
                    break
                
                for repo in page_repos:
                    repos.append({
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "html_url": repo["html_url"],
                        "description": repo.get("description") or "",
                        "private": repo["private"],
                        "default_branch": repo.get("default_branch", "main"),
                    })
                
                # Check if there are more pages
                if len(page_repos) < per_page:
                    break
                
                page += 1
            
            logger.info("Fetched repositories", count=len(repos), username=username or "authenticated user")
            return repos
            
        except Exception as e:
            logger.error("Error fetching repositories", error=str(e))
            return []

    def get_authenticated_user(self) -> Optional[str]:
        """
        Get the authenticated user's username.
        
        Returns:
            Username if successful, None otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers)
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get("login")
            else:
                logger.error("Failed to get authenticated user",
                           status_code=response.status_code)
                return None
        except Exception as e:
            logger.error("Error getting authenticated user", error=str(e))
            return None

    def test_token(self) -> bool:
        """
        Test if the token is valid.
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers)
            return response.status_code == 200
        except Exception:
            return False

