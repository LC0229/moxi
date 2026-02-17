"""Entry point for repository analysis. Delegates to moxi_chunk.repo_analyzer."""

from moxi_chunk.repo_analyzer.main import analyze_repository, main

__all__ = ["analyze_repository", "main"]

if __name__ == "__main__":
    main()
