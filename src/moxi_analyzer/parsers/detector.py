"""Re-export detector from moxi_chunk.repo_analyzer.parsers."""

from moxi_chunk.repo_analyzer.parsers.detector import (
    detect_project_language,
    detect_project_type,
)

__all__ = ["detect_project_language", "detect_project_type"]
