"""
Moxi collection pipeline: gather READMEs + file trees from awesome-readme-style lists.

Output: data/collection/ (JSON) and/or MongoDB readme_samples.
Run: make moxi-collect  or  python -m moxi_collect
"""

from moxi_collect.run import main as run_collection

__all__ = ["run_collection"]
