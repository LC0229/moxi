"""Core business logic for dataset generation (reusable by CLI and API)."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from core import get_logger, settings
from dataset_generator.crawlers import AwesomeListsCrawler, GithubTrendingCrawler
from dataset_generator.crawlers.github_trending import RepositoryInfo as CrawlerRepoInfo
from dataset_generator.generators import InstructionGenerator
from dataset_generator.quality_control import Deduplicator, DatasetValidator
from dataset_generator.utils import read_readme
from repo_analyzer import RepositoryInfo, analyze_repository

logger = get_logger(__name__)


def fetch_repositories(
    source: str = "github",
    min_stars: Optional[int] = None,
    limit: Optional[int] = None,
    languages: Optional[List[str]] = None,
) -> List[CrawlerRepoInfo]:
    """
    Fetch repositories from various sources.
    
    Args:
        source: Source type ("github", "awesome", or "both")
        min_stars: Minimum stars filter
        limit: Maximum number of repos to fetch
        languages: List of programming languages to filter
        
    Returns:
        List of RepositoryInfo objects from crawlers
    """
    repos: List[CrawlerRepoInfo] = []
    
    if source in ["github", "both"]:
        logger.info("Fetching from GitHub Trending")
        github_crawler = GithubTrendingCrawler()
        github_repos = github_crawler.fetch_quality_repos(
            min_stars=min_stars or settings.MIN_REPO_STARS,
            limit=limit or settings.MAX_REPOS_TO_CRAWL,
            languages=languages
        )
        repos.extend(github_repos)
        logger.info("Fetched from GitHub", count=len(github_repos))
    
    if source in ["awesome", "both"]:
        logger.info("Fetching from Awesome Lists")
        awesome_crawler = AwesomeListsCrawler()
        awesome_urls = awesome_crawler.fetch_from_awesome_list(
            "https://github.com/vinta/awesome-python"
        )
        awesome_repos = awesome_crawler.convert_to_repo_info(awesome_urls)
        repos.extend(awesome_repos)
        logger.info("Fetched from Awesome Lists", count=len(awesome_repos))
    
    return repos


def process_single_repository(
    repo_url: str,
    cache_dir: Optional[str] = None,
    instruction_generator: Optional[InstructionGenerator] = None,
) -> Optional[Dict]:
    """
    Process a single repository and generate a training sample.
    
    This is the core function that can be reused by CLI, API, and batch processing.
    
    Args:
        repo_url: GitHub repository URL
        cache_dir: Optional cache directory for cloned repos
        instruction_generator: Optional InstructionGenerator instance
                             (if None, creates a new one)
        
    Returns:
        Training sample dictionary, or None if processing failed
    """
    try:
        logger.info("Processing repository", url=repo_url)
        
        # Step 1: Analyze repository (uses repo_analyzer)
        repo_analysis = analyze_repository(
            repo_url, 
            cache_dir=cache_dir or settings.REPO_CACHE_DIR
        )
        
        # Step 2: Read README
        readme_content = read_readme(repo_analysis)
        if not readme_content:
            logger.warning("Skipping repo without README", url=repo_url)
            return None
        
        # Step 3: Generate training sample
        if instruction_generator is None:
            instruction_generator = InstructionGenerator()
        
        sample = instruction_generator.generate_sample(repo_analysis, readme_content)
        
        logger.info("Sample generated", url=repo_url)
        return sample
        
    except Exception as e:
        logger.error("Failed to process repository", url=repo_url, error=str(e))
        return None


def process_batch_repositories(
    repo_urls: List[str],
    concurrent: bool = True,
    max_workers: int = 50,
    cache_dir: Optional[str] = None,
) -> List[Dict]:
    """
    Process multiple repositories in batch (with optional concurrency).
    
    This function demonstrates high concurrency capabilities.
    
    Args:
        repo_urls: List of GitHub repository URLs
        concurrent: If True, process repositories concurrently
        max_workers: Maximum number of concurrent workers (if concurrent=True)
        cache_dir: Optional cache directory for cloned repos
        
    Returns:
        List of training samples (None values filtered out)
    """
    if not repo_urls:
        return []
    
    logger.info("Processing batch", 
               total=len(repo_urls), 
               concurrent=concurrent,
               max_workers=max_workers if concurrent else 1)
    
    # Create a single InstructionGenerator to reuse (more efficient)
    instruction_generator = InstructionGenerator()
    
    if concurrent:
        # Concurrent processing (high concurrency demonstration)
        training_samples = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(
                    process_single_repository,
                    url,
                    cache_dir,
                    instruction_generator
                ): url
                for url in repo_urls
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    sample = future.result()
                    if sample:
                        training_samples.append(sample)
                        logger.debug("Completed", 
                                   url=url, 
                                   total_samples=len(training_samples))
                except Exception as e:
                    logger.error("Task failed", url=url, error=str(e))
        
        logger.info("Batch processing complete", 
                   total=len(repo_urls),
                   successful=len(training_samples))
        return training_samples
    
    else:
        # Serial processing (for debugging or when concurrency is not desired)
        training_samples = []
        for i, url in enumerate(repo_urls, 1):
            logger.info("Processing", current=i, total=len(repo_urls), url=url)
            sample = process_single_repository(url, cache_dir, instruction_generator)
            if sample:
                training_samples.append(sample)
        return training_samples


def generate_dataset(
    source: str = "github",
    min_stars: Optional[int] = None,
    limit: Optional[int] = None,
    languages: Optional[List[str]] = None,
    concurrent: bool = True,
    max_workers: int = 50,
    skip_generation: bool = False,
) -> Dict:
    """
    Complete dataset generation pipeline.
    
    This is the main function that orchestrates the entire process:
    1. Fetch repositories
    2. Process repositories (analyze + generate samples)
    3. Quality control (deduplicate + validate)
    4. Return results
    
    Args:
        source: Source type ("github", "awesome", or "both")
        min_stars: Minimum stars filter
        limit: Maximum number of repos to fetch
        languages: List of programming languages to filter
        concurrent: If True, process repositories concurrently
        max_workers: Maximum number of concurrent workers
        skip_generation: If True, only fetch repos, don't generate samples
        
    Returns:
        Dictionary with results and statistics
    """
    # Step 1: Fetch repositories
    repos = fetch_repositories(source, min_stars, limit, languages)
    
    if skip_generation:
        return {
            "repos_fetched": len(repos),
            "samples": [],
            "valid_samples": [],
        }
    
    # Step 2: Process repositories (analyze + generate samples)
    repo_urls = [repo.url for repo in repos]
    training_samples = process_batch_repositories(
        repo_urls,
        concurrent=concurrent,
        max_workers=max_workers,
    )
    
    # Step 3: Quality control
    logger.info("Running quality control")
    
    # Deduplicate
    deduplicator = Deduplicator()
    unique_samples = deduplicator.deduplicate(training_samples)
    
    # Validate
    validator = DatasetValidator()
    validation_report = validator.validate_dataset(unique_samples)
    
    # Filter valid samples
    valid_samples = []
    for sample in unique_samples:
        is_valid, _ = validator.validate_sample(sample)
        if is_valid:
            valid_samples.append(sample)
    
    return {
        "repos_fetched": len(repos),
        "samples": training_samples,
        "unique_samples": unique_samples,
        "valid_samples": valid_samples,
        "validation_report": validation_report,
    }

