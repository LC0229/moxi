#!/usr/bin/env python3
"""
Clean invalid repositories from cache and training dataset.

This script:
1. Scans cached repositories and removes invalid ones (content lists, etc.)
2. Removes invalid samples from training dataset
3. Updates validation report
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List

from core import get_logger, settings
from moxi_analyzer.parsers.project_validator import is_valid_coding_project

logger = get_logger(__name__)


def clean_cached_repos(cache_dir: Path) -> int:
    """
    Clean invalid repositories from cache directory.
    
    Args:
        cache_dir: Path to cache directory
        
    Returns:
        Number of repositories removed
    """
    if not cache_dir.exists():
        logger.info("Cache directory does not exist", cache_dir=str(cache_dir))
        return 0
    
    removed_count = 0
    repo_dirs = [d for d in cache_dir.iterdir() if d.is_dir()]
    
    logger.info("Scanning cached repositories", total=len(repo_dirs))
    
    for repo_dir in repo_dirs:
        try:
            # Check if it's a valid coding project
            if not is_valid_coding_project(repo_dir):
                logger.info("Removing invalid repository", repo=str(repo_dir))
                shutil.rmtree(repo_dir)
                removed_count += 1
        except Exception as e:
            logger.warning("Error checking repository", repo=str(repo_dir), error=str(e))
    
    logger.info("Cleaned cached repositories", removed=removed_count, remaining=len(repo_dirs) - removed_count)
    return removed_count


def clean_training_dataset(dataset_path: Path) -> Dict:
    """
    Clean invalid samples from training dataset.
    
    Args:
        dataset_path: Path to training dataset JSON file
        
    Returns:
        Dictionary with cleaning statistics
    """
    if not dataset_path.exists():
        logger.info("Training dataset does not exist", path=str(dataset_path))
        return {"removed": 0, "remaining": 0}
    
    logger.info("Loading training dataset", path=str(dataset_path))
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    
    original_count = len(samples)
    valid_samples = []
    removed_samples = []
    
    logger.info("Validating samples", total=original_count)
    
    for i, sample in enumerate(samples):
        try:
            # Check if sample has repo_path
            if 'input' not in sample or 'repo_path' not in sample['input']:
                logger.debug("Sample missing repo_path", index=i)
                removed_samples.append(i)
                continue
            
            repo_path = Path(sample['input']['repo_path'])
            
            # Check if it's a valid coding project
            if not is_valid_coding_project(repo_path):
                logger.debug("Removing invalid sample", index=i, repo=str(repo_path))
                removed_samples.append(i)
                continue
            
            valid_samples.append(sample)
            
        except Exception as e:
            logger.warning("Error validating sample", index=i, error=str(e))
            removed_samples.append(i)
    
    # Save cleaned dataset
    logger.info("Saving cleaned dataset",
               original=original_count,
               valid=len(valid_samples),
               removed=len(removed_samples))
    
    with open(dataset_path, 'w', encoding='utf-8') as f:
        json.dump(valid_samples, f, indent=2, ensure_ascii=False)
    
    return {
        "original": original_count,
        "valid": len(valid_samples),
        "removed": len(removed_samples),
        "removed_indices": removed_samples,
    }


def main():
    """Main function."""
    logger.info("Starting cleanup of invalid repositories")
    
    # Clean cached repositories
    cache_dir = Path(settings.REPO_CACHE_DIR) if settings.REPO_CACHE_DIR else None
    if cache_dir:
        removed_repos = clean_cached_repos(cache_dir)
        logger.info("Cached repositories cleaned", removed=removed_repos)
    else:
        logger.info("No cache directory configured")
    
    # Clean training dataset
    dataset_path = Path(settings.DATA_DIR) / "sft" / "training_dataset.json"
    if dataset_path.exists():
        stats = clean_training_dataset(dataset_path)
        logger.info("Training dataset cleaned", **stats)
    else:
        logger.info("Training dataset not found", path=str(dataset_path))
    
    logger.info("Cleanup complete")


if __name__ == "__main__":
    main()



