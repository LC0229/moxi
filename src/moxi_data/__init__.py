"""Dataset generator module for README training data.

Provides: repo fetching (GitHub + Awesome lists), repo review UI, and quality control
for README-style training data. README collection itself is in collect_awesome_readme_data.py.
"""

from moxi_data.repo_fetcher import fetch_repositories
from moxi_data.review_backend import RepositoryReviewer
from moxi_data.crawlers import AwesomeListsCrawler, GithubTrendingCrawler
from moxi_data.quality_control import DatasetValidator

__all__ = [
    "fetch_repositories",
    "RepositoryReviewer",
    "GithubTrendingCrawler",
    "AwesomeListsCrawler",
    "DatasetValidator",
]
