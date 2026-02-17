#!/usr/bin/env python3
"""
Migrate local awesome_readme JSON into MongoDB (readme_samples).

Run from repo root:
  python scripts/migrate_readme_to_mongo.py [--file training_data/awesome_readme_clean.json]
  python scripts/migrate_readme_to_mongo.py --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.db.mongo import insert_readme_samples, ping


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate awesome_readme JSON to MongoDB readme_samples")
    parser.add_argument(
        "--file",
        type=Path,
        default=REPO_ROOT / "data" / "collection" / "awesome_readme_clean.json",
        help="Path to JSON file (default: data/collection/awesome_readme_clean.json)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only print count, do not insert")
    args = parser.parse_args()

    path = args.file
    if not path.is_file():
        print(f"File not found: {path}")
        sys.exit(1)

    print(f"Loading {path}...")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Support both { "training_data": [...] } and direct list
    if "training_data" in data:
        docs = data["training_data"]
    elif isinstance(data, list):
        docs = data
    else:
        print("Expected JSON with 'training_data' array or a list")
        sys.exit(1)

    if not docs:
        print("No documents to migrate.")
        sys.exit(0)

    print(f"Found {len(docs)} README samples.")

    if args.dry_run:
        print("Dry run: skipping insert.")
        return

    if not ping():
        print("MongoDB is not reachable. Start with: docker compose up -d mongodb")
        print("Set MONGODB_URI in .env if needed (default: mongodb://moxi:moxi@localhost:27017)")
        sys.exit(1)

    n = insert_readme_samples(docs)
    print(f"Inserted {n} documents into MongoDB readme_samples.")


if __name__ == "__main__":
    main()
