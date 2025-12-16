"""Dataset generator module for creating training datasets."""

from dataset_generator.core import (
    fetch_repositories,
    generate_dataset,
    process_batch_repositories,
    process_single_repository,
)
from dataset_generator.crawlers import AwesomeListsCrawler, GithubTrendingCrawler
from dataset_generator.generators import InstructionGenerator
from dataset_generator.quality_control import Deduplicator, DatasetValidator

__all__ = [
    # Core functions (reusable by CLI and API)
    "process_single_repository",
    "process_batch_repositories",
    "fetch_repositories",
    "generate_dataset",
    # Crawlers
    "GithubTrendingCrawler",
    "AwesomeListsCrawler",
    # Generators
    "InstructionGenerator",
    # Quality control
    "DatasetValidator",
    "Deduplicator",
]

