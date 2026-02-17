"""
Feature step: chunk collection → readme_chunks.json.

Prefer: make moxi-chunk   or   python -m moxi_chunk.run_feature

This script delegates to moxi_chunk (moxi step 2: chunk).
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from moxi_chunk.chunking import run_chunking


def main():
    parser = argparse.ArgumentParser(description="Feature step: chunk collection → features for Phase 3")
    parser.add_argument("--output", "-o", default="data/chunks/readme_chunks.json", help="Output JSON path")
    parser.add_argument("--min-length", type=int, default=1000, help="Min chunk length")
    parser.add_argument("--max-length", type=int, default=2000, help="Max chunk length")
    parser.add_argument("--source", choices=["mongo", "json", "auto"], default="auto", help="Read from mongo, json, or auto")
    parser.add_argument("--json-path", default=None, help="JSON path when source=json")
    args = parser.parse_args()

    n, path = run_chunking(
        output_path=args.output,
        min_length=args.min_length,
        max_length=args.max_length,
        source=args.source,
        json_path=args.json_path,
    )
    print(f"Wrote {n} chunks to {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
