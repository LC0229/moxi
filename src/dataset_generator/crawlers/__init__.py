"""Crawlers for fetching quality repositories for training dataset."""

from dataset_generator.crawlers.github_trending import GithubTrendingCrawler
from dataset_generator.crawlers.awesome_lists import AwesomeListsCrawler

__all__ = ["GithubTrendingCrawler", "AwesomeListsCrawler"]

