"""Awesome Lists crawler for fetching curated repositories."""

import re
from typing import List, Optional
from urllib.parse import urlparse

import requests

from core import get_logger
from core.lib import extract_repo_owner_and_name, validate_github_url
from dataset_generator.crawlers.github_trending import RepositoryInfo

logger = get_logger(__name__)


class AwesomeListsCrawler:
    """Crawler for extracting repositories from Awesome Lists."""

    def __init__(self):
        """Initialize Awesome Lists crawler."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Moxi-Dataset-Generator/1.0"
        })

    def _extract_github_links(self, markdown_content: str) -> List[str]:
        """
        Extract GitHub repository URLs from Markdown content.
        
        Args:
            markdown_content: Markdown text from Awesome List README
            
        Returns:
            List of GitHub repository URLs
        """
        # Pattern to match GitHub URLs in markdown links: [text](https://github.com/owner/repo)
        pattern = r'https://github\.com/[\w\-\.]+/[\w\-\.]+'
        matches = re.findall(pattern, markdown_content)
        
        # Filter valid GitHub URLs
        github_urls = []
        for url in matches:
            if validate_github_url(url):
                # Remove query parameters and fragments
                parsed = urlparse(url)
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
                if clean_url not in github_urls:
                    github_urls.append(clean_url)
        
        return github_urls

    def fetch_from_awesome_list(self, awesome_list_url: str) -> List[str]:
        """
        Fetch repository URLs from an Awesome List.
        
        Args:
            awesome_list_url: URL to Awesome List (e.g., awesome-python)
            
        Returns:
            List of GitHub repository URLs
        """
        logger.info("Fetching from Awesome List", url=awesome_list_url)
        
        try:
            # Convert to raw GitHub content URL if needed
            if "github.com" in awesome_list_url and "raw" not in awesome_list_url:
                # Convert to raw content URL
                awesome_list_url = awesome_list_url.replace(
                    "github.com", "raw.githubusercontent.com"
                ).replace("/blob/", "/")
                
                # If no branch specified, try main/master
                if "/main/README.md" not in awesome_list_url and "/master/README.md" not in awesome_list_url:
                    awesome_list_url = awesome_list_url.rstrip("/") + "/main/README.md"
            
            response = self.session.get(awesome_list_url, timeout=30)
            response.raise_for_status()
            
            markdown_content = response.text
            github_urls = self._extract_github_links(markdown_content)
            
            logger.info("Extracted GitHub URLs", 
                       awesome_list=awesome_list_url, 
                       count=len(github_urls))
            
            return github_urls
            
        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch Awesome List", 
                        url=awesome_list_url, 
                        error=str(e))
            return []

    def fetch_from_multiple_lists(
        self, 
        awesome_list_urls: List[str],
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Fetch repositories from multiple Awesome Lists.
        
        Args:
            awesome_list_urls: List of Awesome List URLs
            limit: Maximum number of unique repositories to return
            
        Returns:
            List of unique GitHub repository URLs
        """
        all_urls: List[str] = []
        
        for url in awesome_list_urls:
            urls = self.fetch_from_awesome_list(url)
            all_urls.extend(urls)
            
            if limit and len(all_urls) >= limit:
                break
        
        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in all_urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)
        
        logger.info("Fetched from multiple Awesome Lists", 
                   total=len(unique_urls), 
                   lists=len(awesome_list_urls))
        
        return unique_urls[:limit] if limit else unique_urls

    def convert_to_repo_info(self, github_urls: List[str]) -> List[RepositoryInfo]:
        """
        Convert GitHub URLs to RepositoryInfo objects.
        
        Args:
            github_urls: List of GitHub repository URLs
            
        Returns:
            List of RepositoryInfo objects (without star counts, will be fetched separately)
        """
        repo_infos = []
        
        for url in github_urls:
            try:
                owner, name = extract_repo_owner_and_name(url)
                repo_info = RepositoryInfo(
                    url=url,
                    owner=owner,
                    name=name,
                    stars=0,  # Will be fetched separately if needed
                    has_readme=True  # Assume Awesome List repos have README
                )
                repo_infos.append(repo_info)
            except Exception as e:
                logger.warning("Failed to parse GitHub URL", url=url, error=str(e))
                continue
        
        return repo_infos

