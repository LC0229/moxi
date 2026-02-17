#!/usr/bin/env python3
"""
Moxi collection pipeline (entrypoint from repo root).

Prefer: make moxi-collect   or   cd src && python -m moxi_collect

Output: data/collection/ (JSON) and/or MongoDB readme_samples.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from moxi_collect.run import main

if __name__ == "__main__":
    sys.exit(main())
