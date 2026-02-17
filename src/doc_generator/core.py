"""Core business logic for document generation (reusable by CLI and API)."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from core import get_logger, settings
from moxi_analyzer import analyze_repository
from doc_generator.llm.architecture_gen import ArchitectureGenerator
from doc_generator.writer import write_to_repo_via_api

logger = get_logger(__name__)


def generate_single_doc(
    repo_url: str,
    auto_write: bool = False,
    file_name: str = "ARCHITECTURE_BY_MOXI.md",
    cache_dir: Optional[str] = None,
    architecture_generator: Optional[ArchitectureGenerator] = None,
) -> Optional[Dict]:
    """
    Generate architecture diagram for a single repository.

    This is the core function that can be reused by CLI, API, and batch processing.

    Args:
        repo_url: GitHub repository URL
        auto_write: If True, automatically write to repository via GitHub API
        file_name: Name of the file to write (default: "ARCHITECTURE_BY_MOXI.md")
        cache_dir: Optional cache directory for cloned repos
        architecture_generator: Optional ArchitectureGenerator instance
                               (if None, creates a new one)

    Returns:
        Dictionary with generated architecture diagram and metadata, or None if failed
    """
    try:
        logger.info("Generating architecture diagram", url=repo_url, auto_write=auto_write)

        # Step 1: Analyze repository (uses moxi_analyzer)
        repo_analysis = analyze_repository(
            repo_url,
            cache_dir=cache_dir or settings.REPO_CACHE_DIR
        )

        # Step 2: Generate architecture diagram using rule-based analysis + GPT-4
        if architecture_generator is None:
            architecture_generator = ArchitectureGenerator()
        architecture_content = architecture_generator.generate(repo_analysis)

        if not architecture_content:
            logger.warning("Failed to generate architecture diagram", url=repo_url)
            return None

        # Step 3: Write to repository if auto_write is True
        if auto_write:
            success = write_to_repo_via_api(
                repo_url=repo_url,
                content=architecture_content,
                file_path=file_name,
            )
            if not success:
                logger.warning("Failed to write to repository", url=repo_url)
                return {
                    "repo_url": repo_url,
                    "architecture_content": architecture_content,
                    "file_name": file_name,  # Add file_name even on failure
                    "written": False,
                    "error": "Failed to write via GitHub API",
                }

        logger.info("Architecture diagram generated", url=repo_url, written=auto_write, file_name=file_name)
        return {
            "repo_url": repo_url,
            "architecture_content": architecture_content,
            "file_name": file_name,
            "written": auto_write,
            "repo_info": {
                "project_type": repo_analysis.project_type.value,
                "key_files": {k: str(v) for k, v in repo_analysis.key_files.items()},
            },
        }

    except Exception as e:
        logger.error("Failed to generate architecture diagram", url=repo_url, error=str(e))
        return None


def generate_batch_docs(
    repo_urls: List[str],
    auto_write: bool = False,
    file_name: str = "ARCHITECTURE_BY_MOXI.md",
    concurrent: bool = True,
    max_workers: int = 10,
    cache_dir: Optional[str] = None,
) -> List[Dict]:
    """
    Generate architecture diagrams for multiple repositories in batch (with optional concurrency).

    This function demonstrates high concurrency capabilities.

    Args:
        repo_urls: List of GitHub repository URLs
        auto_write: If True, automatically write to repositories via GitHub API
        file_name: Name of the file to write (default: "ARCHITECTURE_BY_MOXI.md")
        concurrent: If True, process repositories concurrently
        max_workers: Maximum number of concurrent workers (if concurrent=True)
        cache_dir: Optional cache directory for cloned repos

    Returns:
        List of results (None values filtered out)
    """
    if not repo_urls:
        return []

    logger.info("Processing batch",
               total=len(repo_urls),
               concurrent=concurrent,
               max_workers=max_workers if concurrent else 1,
               auto_write=auto_write)

    # Create a single architecture generator to reuse (more efficient)
    architecture_generator = ArchitectureGenerator()

    if concurrent:
        # Concurrent processing (high concurrency demonstration)
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(
                    generate_single_doc,
                    url,
                    auto_write,
                    file_name,
                    cache_dir,
                    architecture_generator
                ): url
                for url in repo_urls
            }

            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        logger.debug("Completed",
                                   url=url,
                                   total_results=len(results))
                except Exception as e:
                    logger.error("Task failed", url=url, error=str(e))

        logger.info("Batch processing complete",
                   total=len(repo_urls),
                   successful=len(results))
        return results

    else:
        # Serial processing (for debugging or when concurrency is not desired)
        results = []
        for i, url in enumerate(repo_urls, 1):
            logger.info("Processing", current=i, total=len(repo_urls), url=url)
            result = generate_single_doc(url, auto_write, file_name, cache_dir, None)
            if result:
                results.append(result)
        return results

