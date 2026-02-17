"""Crawlers for fetching repositories from various sources."""

from moxi_chunk.repo_analyzer.crawlers.github import GithubCrawler
from moxi_chunk.repo_analyzer.crawlers.local import LocalCrawler

__all__ = ["GithubCrawler", "LocalCrawler"]

