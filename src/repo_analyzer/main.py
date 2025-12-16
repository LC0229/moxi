"""Entry point for repository analysis."""

from pathlib import Path
import argparse

from core import get_logger, settings
from core.errors import RepositoryNotFound
from repo_analyzer.crawlers import GithubCrawler, LocalCrawler
from repo_analyzer.models import RepositoryInfo
from repo_analyzer.parsers.detector import detect_project_type
from repo_analyzer.parsers.file_analyzer import find_key_files
from repo_analyzer.parsers.tree_builder import list_files

logger = get_logger(__name__)


def analyze_repository(path_or_url: str, cache_dir: str | None = None) -> RepositoryInfo:
    """
    Analyze a repository from a GitHub URL or local path.
    
    Args:
        path_or_url: GitHub URL or local path to repository
        cache_dir: Optional directory to cache cloned repositories.
                  If None, uses temporary directory (no caching).
    """
    repo_path: Path
    if path_or_url.startswith("http"):
        repo_path = GithubCrawler(cache_dir=cache_dir).fetch(path_or_url)
    else:
        repo_path = LocalCrawler().fetch(path_or_url)

    files = list_files(repo_path)
    key_files = find_key_files(repo_path, files)
    project_type = detect_project_type(files)

    return RepositoryInfo(
        path=repo_path,
        project_type=project_type,
        key_files=key_files,
        all_files=list(files),
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a repository")
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub URL or local path to repository",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    try:
        # Use cache directory from settings if available
        cache_dir = getattr(settings, "REPO_CACHE_DIR", None)
        repo = analyze_repository(args.repo, cache_dir=cache_dir)
        logger.info(
            "Analysis complete",
            path=str(repo.path),
            project_type=repo.project_type.value,
            key_files=list(repo.key_files.keys()),
        )
        # Print minimal summary for CLI usage
        print(f"Project type: {repo.project_type.value}")
        print("Key files:")
        for name, path in repo.key_files.items():
            print(f"  - {name}: {path}")
    except RepositoryNotFound as e:
        logger.error("Analysis failed", error=str(e))
        raise


if __name__ == "__main__":
    main()

