"""Crawlers for fetching repositories from various sources."""

from repo_analyzer.crawlers.github import GithubCrawler
from repo_analyzer.crawlers.local import LocalCrawler

__all__ = ["GithubCrawler", "LocalCrawler"]

