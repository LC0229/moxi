"""Crawlers for fetching quality repositories for training dataset."""

from moxi_data.crawlers.github_repo_crawler import GithubTrendingCrawler
from moxi_data.crawlers.awesome_list_crawler import AwesomeListsCrawler

__all__ = ["GithubTrendingCrawler", "AwesomeListsCrawler"]

