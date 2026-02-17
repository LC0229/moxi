"""Clean and validate README training data.

Backup, filter by minimum readme/content length, and save cleaned JSON + report.
"""

import argparse
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from core import get_logger, settings

logger = get_logger(__name__)

# Minimum length for readme or content to count as valid (chars)
DEFAULT_MIN_README_LENGTH = 200


def load_existing_samples(data_dir: Path) -> List[Dict]:
    """
    Load existing training samples from directory.
    
    Supports:
    - Single JSON file (e.g. awesome_readme_clean.json or training_data with "training_data" key)
    - Directory of JSON files
    """
    samples = []
    
    # Check if it's a single file
    if data_dir.is_file():
        logger.info("Loading from single file", file=str(data_dir))
        with open(data_dir, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                samples = data
            elif isinstance(data, dict) and "training_data" in data:
                samples = data["training_data"]
            elif isinstance(data, dict) and "samples" in data:
                samples = data["samples"]
            else:
                samples = [data]
        return samples
    
    # Check if it's a directory
    if data_dir.is_dir():
        logger.info("Loading from directory", dir=str(data_dir))
        json_files = list(data_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    sample = json.load(f)
                    samples.append(sample)
            except Exception as e:
                logger.warning("Failed to load file", file=str(json_file), error=str(e))
        
        return samples
    
    logger.error("Invalid data path", path=str(data_dir))
    return []


def validate_and_clean(
    data_path: str,
    min_quality_score: float = 0.7,
    backup: bool = True,
    delete_low_quality: bool = False,
    output_dir: Optional[str] = None,
    min_readme_length: int = DEFAULT_MIN_README_LENGTH,
) -> Dict:
    """
    Validate and clean README training data: keep samples with readme/content above min length.
    """
    data_path_obj = Path(data_path)

    if not data_path_obj.exists():
        logger.error("Data path does not exist", path=data_path)
        return {"error": "Path does not exist"}

    logger.info("Loading existing samples...")
    samples = load_existing_samples(data_path_obj)

    if not samples:
        logger.warning("No samples found", path=data_path)
        return {"error": "No samples found"}

    logger.info("Loaded samples", count=len(samples))

    if backup:
        backup_path = Path(data_path).parent / f"{Path(data_path).stem}_backup.json"
        if data_path_obj.is_file():
            shutil.copy2(data_path_obj, backup_path)
            logger.info("Backup created", backup=str(backup_path))
        elif data_path_obj.is_dir():
            backup_dir = data_path_obj.parent / f"{data_path_obj.name}_backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(data_path_obj, backup_dir)
            logger.info("Backup created", backup=str(backup_dir))

    logger.info("Validating README samples (min length=%s)...", min_readme_length)
    valid_samples = []
    invalid_samples = []
    low_quality_samples = []

    for i, sample in enumerate(samples, 1):
        if i % 100 == 0:
            logger.info("Validation progress", current=i, total=len(samples))

        text = sample.get("readme") or sample.get("content") or sample.get("output") or ""
        if not isinstance(text, str):
            text = str(text) if text else ""
        length = len(text)

        if length < min_readme_length:
            low_quality_samples.append({
                "index": i,
                "reason": f"readme/content length {length} < {min_readme_length}",
            })
            continue
        valid_samples.append(sample)

    report = {
        "total_samples": len(samples),
        "valid_samples": len(valid_samples),
        "invalid_samples": len(invalid_samples),
        "low_quality_samples": len(low_quality_samples),
        "removed_count": len(invalid_samples) + len(low_quality_samples),
        "retention_rate": len(valid_samples) / len(samples) if samples else 0,
    }
    
    logger.info("Validation complete", **report)
    
    # Save cleaned data
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if data_path_obj.is_file():
            # Save as single file
            output_file = output_path / "cleaned_training_dataset.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(valid_samples, f, indent=2, ensure_ascii=False)
            logger.info("Cleaned data saved", file=str(output_file))
        else:
            # Save as directory of files
            for i, sample in enumerate(valid_samples):
                repo_url = sample.get("metadata", {}).get("repo_url", f"sample_{i}")
                repo_name = repo_url.split("/")[-1].replace(".git", "")
                owner = repo_url.split("/")[-2] if "/" in repo_url else "unknown"
                filename = f"{owner}_{repo_name}.json"
                filename = "".join(c for c in filename if c.isalnum() or c in "._-")
                
                output_file = output_path / filename
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(sample, f, indent=2, ensure_ascii=False)
            
            logger.info("Cleaned data saved", dir=str(output_path), count=len(valid_samples))
    
    # Delete low-quality if requested
    if delete_low_quality and (invalid_samples or low_quality_samples):
        logger.warning("Deleting low-quality samples is not implemented for file-based storage")
        logger.info("Use --output-dir to save cleaned data separately")
    
    # Save report
    report_path = Path(data_path).parent / "cleaning_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info("Cleaning report saved", file=str(report_path))
    
    return report


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Clean and validate existing training data"
    )
    
    parser.add_argument(
        "--data-path",
        type=str,
        default=str(Path(settings.DATA_DIR) / "collection" / "awesome_readme_clean.json"),
        help="Path to training data (file or directory)"
    )
    
    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.7,
        help="Ignored (kept for CLI compat); use --min-length"
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=DEFAULT_MIN_README_LENGTH,
        help="Minimum readme/content length in chars (default: 200)"
    )
    
    parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Backup before cleaning (default: True)"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't backup before cleaning"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for cleaned data (default: same as input)"
    )
    
    parser.add_argument(
        "--delete-low-quality",
        action="store_true",
        help="Delete low-quality samples (use with caution!)"
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = _parse_args()
    
    # Handle backup flag
    backup = args.backup and not args.no_backup
    
    logger.info("Starting data cleaning",
               data_path=args.data_path,
               min_quality=args.min_quality,
               backup=backup)
    
    report = validate_and_clean(
        data_path=args.data_path,
        backup=backup,
        delete_low_quality=args.delete_low_quality,
        output_dir=args.output_dir,
        min_readme_length=args.min_length,
    )

    print("\n" + "=" * 60)
    print("README data cleaning report")
    print("=" * 60)
    print(f"Total samples: {report.get('total_samples', 0)}")
    print(f"Valid samples: {report.get('valid_samples', 0)}")
    print(f"Low-quality (short): {report.get('low_quality_samples', 0)}")
    print(f"Removed: {report.get('removed_count', 0)}")
    print(f"Retention rate: {report.get('retention_rate', 0):.1%}")
    print("=" * 60)


if __name__ == "__main__":
    main()

