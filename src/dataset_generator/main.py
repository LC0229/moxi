"""Main entry point for dataset generation pipeline (CLI interface)."""

import argparse
import json
from pathlib import Path

from core import get_logger, settings
from core.lib import ensure_dir_exists
from dataset_generator.core import generate_dataset, fetch_repositories

logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate training dataset")
    parser.add_argument(
        "--source",
        choices=["github", "awesome", "both"],
        default="github",
        help="Source for repositories (default: github)",
    )
    parser.add_argument(
        "--min-stars",
        type=int,
        default=None,
        help=f"Minimum stars (default: {settings.MIN_REPO_STARS})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=f"Maximum repos to fetch (default: {settings.MAX_REPOS_TO_CRAWL})",
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        help="Programming languages to filter (e.g., Python JavaScript)",
    )
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip GPT-4 generation (only fetch repos)",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for dataset generation (CLI)."""
    args = _parse_args()
    
    logger.info("Starting dataset generation", 
               source=args.source,
               min_stars=args.min_stars or settings.MIN_REPO_STARS,
               limit=args.limit or settings.MAX_REPOS_TO_CRAWL)
    
    # Save repository list (before generation)
    if not args.skip_generation:
        repos = fetch_repositories(
            source=args.source,
            min_stars=args.min_stars,
            limit=args.limit,
            languages=args.languages
        )
        output_dir = Path(settings.DATA_DIR) / "repo_list"
        ensure_dir_exists(output_dir)
        repo_list_file = output_dir / "repositories.json"
        with open(repo_list_file, "w") as f:
            json.dump([r.model_dump() for r in repos], f, indent=2)
        logger.info("Repository list saved", file=str(repo_list_file))
    
    # Call core function (reusable by CLI and future API)
    results = generate_dataset(
        source=args.source,
        min_stars=args.min_stars,
        limit=args.limit,
        languages=args.languages,
        concurrent=True,  # Enable concurrency for high performance
        max_workers=50,   # Process 50 repos simultaneously
        skip_generation=args.skip_generation,
    )
    
    if args.skip_generation:
        print(f"✅ Fetched {results['repos_fetched']} repositories")
        return
    
    # Save results
    dataset_dir = Path(settings.TRAINING_DATA_DIR)
    ensure_dir_exists(dataset_dir)
    
    dataset_file = dataset_dir / "training_dataset.json"
    with open(dataset_file, "w") as f:
        json.dump(results["valid_samples"], f, indent=2)
    
    report_file = dataset_dir / "validation_report.json"
    with open(report_file, "w") as f:
        json.dump(results["validation_report"], f, indent=2)
    
    # Print summary
    logger.info("Dataset generation complete", 
               total_repos=results["repos_fetched"],
               valid_samples=len(results["valid_samples"]),
               dataset_file=str(dataset_file))
    
    print(f"✅ Fetched {results['repos_fetched']} repositories")
    print(f"✅ Generated {len(results['samples'])} training samples")
    print(f"✅ After deduplication: {len(results['unique_samples'])} unique samples")
    print(f"✅ After validation: {len(results['valid_samples'])} valid samples")
    print(f"✅ Saved to {dataset_file}")
    print(f"✅ Validation report: {report_file}")

if __name__ == "__main__":
    main()

