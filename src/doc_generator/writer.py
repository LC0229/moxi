"""Writer module for writing documentation to repositories."""

import base64
from typing import Optional

import requests

from core import get_logger, settings
from core.lib import extract_repo_owner_and_name

logger = get_logger(__name__)


def write_to_repo_via_api(
    repo_url: str,
    content: str,
    file_path: str = "README.md",
    branch: str = "main",
    commit_message: Optional[str] = None,
) -> bool:
    """
    Write content to a repository file using GitHub API.
    
    This function uses GitHub API to directly write files to a repository
    without needing to clone or have local access.
    
    Args:
        repo_url: GitHub repository URL (e.g., "https://github.com/user/repo")
        content: File content to write
        file_path: Path to file in repository (default: "README.md")
        branch: Branch name (default: "main")
        commit_message: Commit message (default: auto-generated)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not settings.GITHUB_TOKEN:
            logger.error("GitHub token is required for writing to repository")
            return False
        
        # Extract owner and repo name
        owner, repo = extract_repo_owner_and_name(repo_url)
        if not owner or not repo:
            logger.error("Invalid repository URL", url=repo_url)
            return False
        
        # GitHub API endpoint
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        
        headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        # Check if file exists (to get SHA for update)
        response = requests.get(api_url, headers=headers, params={"ref": branch})
        
        sha = None
        if response.status_code == 200:
            # File exists, get SHA for update
            sha = response.json().get("sha")
            logger.info("File exists, will update", file=file_path, sha=sha[:8])
        elif response.status_code == 404:
            # File doesn't exist, will create new
            logger.info("File does not exist, will create", file=file_path)
        else:
            logger.error("Failed to check file existence", 
                        status_code=response.status_code,
                        response=response.text)
            return False
        
        # Encode content to base64
        content_bytes = content.encode("utf-8")
        content_base64 = base64.b64encode(content_bytes).decode("utf-8")
        
        # Prepare commit message
        if not commit_message:
            if sha:
                commit_message = f"docs: Auto-update {file_path} using Moxi"
            else:
                commit_message = f"docs: Auto-generate {file_path} using Moxi"
        
        # Prepare request data
        data = {
            "message": commit_message,
            "content": content_base64,
            "branch": branch,
        }
        
        if sha:
            data["sha"] = sha
        
        # Create or update file
        response = requests.put(api_url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            logger.info("Successfully wrote to repository",
                       repo_url=repo_url,
                       file=file_path,
                       commit_url=response.json().get("commit", {}).get("html_url"))
            return True
        else:
            logger.error("Failed to write to repository",
                        status_code=response.status_code,
                        response=response.text)
            return False
            
    except Exception as e:
        logger.error("Error writing to repository", error=str(e))
        return False


def write_to_local(
    file_path: str,
    content: str,
) -> bool:
    """
    Write content to a local file.
    
    Args:
        file_path: Local file path
        content: Content to write
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from pathlib import Path
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        path.write_text(content, encoding="utf-8")
        
        logger.info("Successfully wrote to local file", file=file_path)
        return True
        
    except Exception as e:
        logger.error("Error writing to local file", file=file_path, error=str(e))
        return False

