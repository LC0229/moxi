"""Validate if a repository is a valid coding project."""

from pathlib import Path
from typing import Optional

from core import get_logger

logger = get_logger(__name__)


def is_valid_coding_project(
    repo_path: Path,
    repo_info: Optional[dict] = None,
    min_py_files: int = 5,
    min_code_ratio: float = 0.25,
) -> bool:
    """
    Validate if a repository is a valid Python coding project.
    
    Filters out:
    - Content list projects (awesome, list, books, resources)
    - Documentation-only projects
    - Learning material projects
    
    Args:
        repo_path: Path to the repository
        repo_info: Optional GitHub API repo info (for description/topics filtering)
        min_py_files: Minimum number of Python files required
        min_code_ratio: Minimum ratio of code files to total files
    
    Returns:
        True if valid coding project, False otherwise
    """
    try:
        # Step 1: Check description and topics (if available)
        if repo_info:
            description = (repo_info.get("description") or "").lower()
            topics = repo_info.get("topics", [])
            
            # Exclude keywords in description
            exclude_keywords = [
                "awesome",
                "list",
                "books",
                "resources",
                "curated",
                "collection",
                "learning",
                "tutorial",
                "course",
                "education",
            ]
            
            if any(keyword in description for keyword in exclude_keywords):
                logger.debug("Excluded: description contains exclude keywords",
                           repo=str(repo_path),
                           description=description[:100])
                return False
            
            # Exclude topics
            if any(topic.lower() in exclude_keywords for topic in topics):
                logger.debug("Excluded: topics contain exclude keywords",
                           repo=str(repo_path),
                           topics=topics)
                return False
        
        # Step 2: Check repository name
        repo_name = repo_path.name.lower()
        exclude_name_keywords = ["awesome", "list", "books", "resources", "curated"]
        if any(keyword in repo_name for keyword in exclude_name_keywords):
            logger.debug("Excluded: repository name contains exclude keywords",
                       repo=str(repo_path))
            return False
        
        # Step 3: Check file structure
        try:
            from moxi_chunk.repo_analyzer.parsers.tree_builder import list_files
            relative_files = list(list_files(repo_path))
            # Convert relative paths to absolute paths
            files = [repo_path / f for f in relative_files]
            # Filter out directories and hidden files
            files = [
                f for f in files
                if f.is_file() and not f.name.startswith(".")
            ]
        except Exception as e:
            logger.warning("Failed to list files", repo=str(repo_path), error=str(e))
            return False
        
        if not files:
            logger.debug("Excluded: no files found", repo=str(repo_path))
            return False
        
        # Step 4: Check Python files count
        py_files = [f for f in files if f.suffix == ".py"]
        if len(py_files) < min_py_files:
            logger.debug("Excluded: insufficient Python files",
                       repo=str(repo_path),
                       py_files=len(py_files),
                       required=min_py_files)
            return False
        
        # Step 5: Check code file ratio
        code_extensions = {".py", ".js", ".java", ".go", ".rs", ".cpp", ".c", ".ts", ".tsx"}
        code_files = [f for f in files if f.suffix in code_extensions]
        code_ratio = len(code_files) / len(files) if files else 0
        
        if code_ratio < min_code_ratio:
            logger.debug("Excluded: low code file ratio",
                       repo=str(repo_path),
                       code_ratio=f"{code_ratio:.2%}",
                       required=f"{min_code_ratio:.2%}")
            return False
        
        # Step 6: Check project structure indicators
        file_names = {f.name.lower() for f in files}
        file_paths = {str(f.relative_to(repo_path)).lower() for f in files}
        
        has_structure = any([
            "src/" in p for p in file_paths if "/" in p
        ]) or any([
            name in file_names
            for name in ["__init__.py", "setup.py", "pyproject.toml", "requirements.txt"]
        ])
        
        if not has_structure:
            logger.debug("Excluded: no project structure indicators",
                       repo=str(repo_path))
            return False
        
        logger.debug("Valid coding project",
                   repo=str(repo_path),
                   py_files=len(py_files),
                   code_ratio=f"{code_ratio:.2%}")
        return True
        
    except Exception as e:
        logger.error("Error validating project", repo=str(repo_path), error=str(e))
        return False

