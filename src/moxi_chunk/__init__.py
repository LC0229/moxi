"""
Moxi chunk: chunk READMEs from collection + repo analysis (file tree, key files).

- chunking: read collection (Mongo/JSON), chunk READMEs → data/chunks/.
- repo_analyzer: given a repo URL/path → file tree, key files, project type/language.
"""

from moxi_chunk.chunking import run_chunking
from moxi_chunk.repo_analyzer.main import analyze_repository

__all__ = ["run_chunking", "analyze_repository"]
