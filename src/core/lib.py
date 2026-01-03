"""Common utility functions for Moxi project."""

from pathlib import Path
from typing import Any

from core.errors import ImproperlyConfigured


def flatten(nested_list: list) -> list:
    """
    Flatten a list of lists into a single list.
    
    Args:
        nested_list: A list containing other lists
        
    Returns:
        A flattened single-level list
        
    Example:
        >>> flatten([[1, 2], [3, 4], [5]])
        [1, 2, 3, 4, 5]
    """
    return [item for sublist in nested_list for item in sublist]


def ensure_dir_exists(path: str | Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory
        
    Returns:
        Path object pointing to the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def validate_github_url(url: str) -> bool:
    """
    Validate if a string is a valid GitHub repository URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if valid GitHub URL, False otherwise
        
    Example:
        >>> validate_github_url("https://github.com/user/repo")
        True
        >>> validate_github_url("https://gitlab.com/user/repo")
        False
    """
    if not url:
        return False
    
    valid_patterns = [
        "https://github.com/",
        "http://github.com/",
        "git@github.com:",
    ]
    
    return any(url.startswith(pattern) for pattern in valid_patterns)


def extract_repo_owner_and_name(github_url: str) -> tuple[str, str]:
    """
    Extract owner and repository name from a GitHub URL.
    
    This function only extracts the owner and repo name, ignoring any path,
    query parameters, or fragments that may follow.
    
    Args:
        github_url: A GitHub repository URL (may include paths, query params, etc.)
        
    Returns:
        A tuple of (owner, repo_name)
        
    Raises:
        ImproperlyConfigured: If the URL is invalid
        
    Example:
        >>> extract_repo_owner_and_name("https://github.com/pytorch/pytorch")
        ('pytorch', 'pytorch')
        >>> extract_repo_owner_and_name("https://github.com/user/repo/.github/workflows")
        ('user', 'repo')
        >>> extract_repo_owner_and_name("https://github.com/user/repo.git?branch=main")
        ('user', 'repo')
    """
    if not validate_github_url(github_url):
        raise ImproperlyConfigured(f"Invalid GitHub URL: {github_url}")
    
    # Clean the URL - remove trailing slashes, query params, fragments, and .git
    url = github_url.rstrip("/")
    
    # Remove query parameters and fragments
    if "?" in url:
        url = url.split("?")[0]
    if "#" in url:
        url = url.split("#")[0]
    
    # Remove .git suffix if present
    url = url.replace(".git", "")
    
    # Handle different URL formats
    if url.startswith("git@github.com:"):
        # git@github.com:user/repo
        path_part = url.replace("git@github.com:", "")
    else:
        # https://github.com/user/repo or https://github.com/user/repo/path/to/file
        if "github.com/" not in url:
            raise ImproperlyConfigured(f"Cannot find 'github.com/' in URL: {github_url}")
        path_part = url.split("github.com/")[1]
    
    # Split path and only take first two parts (owner and repo)
    # Ignore any additional path segments
    parts = [p for p in path_part.split("/") if p]  # Filter out empty strings
    
    if len(parts) < 2:
        raise ImproperlyConfigured(
            f"Cannot extract owner and name from: {github_url}. "
            f"Expected format: https://github.com/owner/repo"
        )
    
    # Only take the first two parts (owner and repo_name)
    # Ignore any additional path segments (e.g., .github/workflows)
    owner = parts[0]
    repo_name = parts[1]
    
    return owner, repo_name


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: The string to truncate
        max_length: Maximum length of the output string
        suffix: Suffix to append if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def count_tokens_approximate(text: str) -> int:
    """
    Approximate token count using simple heuristic.
    Note: This is a rough estimate. For precise counts, use tiktoken.
    
    Args:
        text: The text to count tokens for
        
    Returns:
        Approximate token count
    """
    # Rough estimate: 1 token ≈ 4 characters for English text
    return len(text) // 4

