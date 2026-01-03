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
    github_token: Optional[str] = None,
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
        github_token: GitHub token (if None, uses settings.GITHUB_TOKEN)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        token = github_token or settings.GITHUB_TOKEN
        if not token:
            logger.error("GitHub token is required for writing to repository")
            return False
        
        # Special check for .github/workflows directory
        # GitHub requires 'workflow' scope (or 'repo' scope which includes it)
        # for writing to .github/workflows directory
        if ".github/workflows" in file_path or file_path.startswith(".github/"):
            logger.warning("Writing to .github directory requires 'workflow' scope",
                         file_path=file_path,
                         hint="Make sure your GitHub token has 'workflow' scope or 'repo' scope (not just 'public_repo')")
        
        # Extract owner and repo name
        owner, repo = extract_repo_owner_and_name(repo_url)
        if not owner or not repo:
            logger.error("Invalid repository URL", url=repo_url)
            return False
        
        # GitHub API endpoint
        # URL encode the file path to handle special characters and nested directories
        # Note: GitHub API requires each path segment to be encoded separately
        from urllib.parse import quote
        # Split path and encode each segment, then join with /
        path_parts = file_path.split("/")
        encoded_parts = [quote(part, safe="") for part in path_parts]
        encoded_file_path = "/".join(encoded_parts)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{encoded_file_path}"
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",  # Add API version header
        }
        
        logger.debug("API URL constructed", 
                    owner=owner, 
                    repo=repo, 
                    file_path=file_path,
                    encoded_path=encoded_file_path,
                    api_url=api_url)
        
        # Check if file exists (to get SHA for update)
        # Note: If branch is not specified or invalid, GitHub API uses default branch
        logger.debug("Checking file existence", file=file_path, branch=branch, url=api_url)
        response = requests.get(api_url, headers=headers, params={"ref": branch})
        
        sha = None
        if response.status_code == 200:
            # File exists, get SHA for update
            sha = response.json().get("sha")
            logger.info("File exists, will update", file=file_path, branch=branch, sha=sha[:8] if sha else "None")
        elif response.status_code == 404:
            # File doesn't exist, will create new
            # But first, ensure all parent directories exist
            # GitHub API can't create nested paths directly, so we need to create directories first
            from pathlib import Path
            file_path_obj = Path(file_path)
            
            # Build list of all parent directories (from root to immediate parent)
            # e.g., for ".github/workflows/file.yml", we need: [".github", ".github/workflows"]
            parent_dirs = []
            current_path = file_path_obj.parent
            while current_path != Path(".") and current_path != Path("/"):
                parent_dirs.insert(0, str(current_path))
                current_path = current_path.parent
            
            # Check and create each parent directory if needed
            for parent_dir in parent_dirs:
                parent_dir_encoded = "/".join([quote(part, safe="") for part in parent_dir.split("/")])
                parent_api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{parent_dir_encoded}"
                parent_response = requests.get(parent_api_url, headers=headers, params={"ref": branch})
                
                if parent_response.status_code == 404:
                    # Directory doesn't exist, create it by creating a .gitkeep file
                    logger.info("Parent directory doesn't exist, creating it", parent_dir=parent_dir)
                    gitkeep_path = f"{parent_dir}/.gitkeep"
                    gitkeep_encoded = "/".join([quote(part, safe="") for part in gitkeep_path.split("/")])
                    gitkeep_api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{gitkeep_encoded}"
                    gitkeep_content = base64.b64encode(b"# Directory created by Moxi\n").decode("utf-8")
                    gitkeep_data = {
                        "message": f"chore: Create {parent_dir} directory",
                        "content": gitkeep_content,
                        "branch": branch,
                    }
                    gitkeep_response = requests.put(gitkeep_api_url, headers=headers, json=gitkeep_data)
                    if gitkeep_response.status_code not in [200, 201]:
                        logger.warning("Failed to create parent directory",
                                     parent_dir=parent_dir,
                                     status_code=gitkeep_response.status_code,
                                     response=gitkeep_response.text[:200])
                        # Continue anyway - maybe the directory was created by another process
                    else:
                        logger.info("Successfully created parent directory", parent_dir=parent_dir)
                elif parent_response.status_code == 200:
                    # Check if response is a directory (array) or a file (object)
                    parent_data = parent_response.json()
                    if isinstance(parent_data, list):
                        # It's a directory (array of files)
                        logger.debug("Parent directory already exists", parent_dir=parent_dir)
                    elif isinstance(parent_data, dict):
                        # It's a file, not a directory - this shouldn't happen for a directory path
                        logger.warning("Parent path points to a file, not a directory",
                                     parent_dir=parent_dir,
                                     file_name=parent_data.get("name"))
                        # This is unusual, but we'll continue anyway
                    else:
                        logger.debug("Parent directory already exists", parent_dir=parent_dir)
                else:
                    logger.warning("Unexpected status when checking parent directory",
                                 parent_dir=parent_dir,
                                 status_code=parent_response.status_code)
            
            logger.info("File does not exist, will create", file=file_path, branch=branch)
        else:
            logger.error("Failed to check file existence", 
                        status_code=response.status_code,
                        branch=branch,
                        response=response.text[:200])
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
        
        # Add committer information (recommended by GitHub API docs)
        # This may be required for certain directories like .github
        # Try to get committer info from git config, or use defaults
        try:
            import subprocess
            git_name = subprocess.check_output(
                ["git", "config", "user.name"], 
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            git_email = subprocess.check_output(
                ["git", "config", "user.email"], 
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            if git_name and git_email:
                data["committer"] = {
                    "name": git_name,
                    "email": git_email,
                }
                logger.debug("Added committer info", name=git_name, email=git_email)
        except Exception:
            # If git config is not available, use defaults
            # GitHub will use the token owner's info if not provided
            pass
        
        # Create or update file
        logger.info("Writing file", 
                   file=file_path, 
                   branch=branch, 
                   has_sha=sha is not None,
                   api_url=api_url,
                   encoded_path=encoded_file_path)
        logger.debug("Request data", 
                    message=data.get("message"),
                    content_length=len(data.get("content", "")),
                    has_sha="sha" in data)
        
        response = requests.put(api_url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            logger.info("Successfully wrote to repository",
                       repo_url=repo_url,
                       file=file_path,
                       branch=branch,
                       commit_url=response.json().get("commit", {}).get("html_url"))
            return True
        else:
            error_response = response.text[:500] if response.text else "No response body"
            error_json = {}
            try:
                error_json = response.json()
            except:
                pass
            
            error_message = error_json.get("message", "Unknown error")
            
            # Check for common permission issues
            if response.status_code == 409:
                # 409 Conflict: SHA mismatch - file was modified
                # Try to get the latest SHA and retry
                logger.warning("SHA mismatch (409 Conflict), retrying with latest SHA",
                             file=file_path,
                             branch=branch)
                # Get latest SHA
                get_response = requests.get(api_url, headers=headers, params={"ref": branch})
                if get_response.status_code == 200:
                    latest_sha = get_response.json().get("sha")
                    if latest_sha and latest_sha != sha:
                        logger.info("Retrying with latest SHA", old_sha=sha[:8] if sha else "None", new_sha=latest_sha[:8])
                        data["sha"] = latest_sha
                        # Retry once
                        retry_response = requests.put(api_url, headers=headers, json=data)
                        if retry_response.status_code in [200, 201]:
                            logger.info("Successfully wrote to repository after retry",
                                       repo_url=repo_url,
                                       file=file_path,
                                       branch=branch)
                            return True
                        else:
                            logger.error("Retry also failed",
                                       status_code=retry_response.status_code,
                                       response=retry_response.text[:200])
                logger.error("Failed to write to repository - SHA mismatch (409 Conflict)",
                            repo_url=repo_url,
                            file=file_path,
                            branch=branch,
                            status_code=response.status_code,
                            error_message=error_message,
                            hint="File was modified between getting SHA and writing. This can happen if multiple workflows run simultaneously.")
            elif response.status_code == 404:
                # Special handling for .github directory
                if ".github" in file_path:
                    logger.error("Failed to write to .github directory - Special handling needed:",
                                repo_url=repo_url,
                                file=file_path,
                                branch=branch,
                                status_code=response.status_code,
                                error_message=error_message,
                                api_url=api_url,
                                encoded_path=encoded_file_path,
                                hint="GitHub may have special restrictions for .github directory. Try: 1) Ensure directory exists, 2) Check if file already exists with different name, 3) Verify branch name is correct")
                elif "Not Found" in error_message:
                    logger.error("Failed to write to repository - Possible causes:",
                                repo_url=repo_url,
                                file=file_path,
                                branch=branch,
                                status_code=response.status_code,
                                error_message=error_message,
                                api_url=api_url,
                                encoded_path=encoded_file_path,
                                hint="Check: 1) Token has 'repo' scope (not just 'public_repo'), 2) Branch exists, 3) Token has write permissions, 4) Parent directory exists")
                else:
                    logger.error("Failed to write to repository",
                                repo_url=repo_url,
                                file=file_path,
                                branch=branch,
                                status_code=response.status_code,
                                api_url=api_url,
                                encoded_path=encoded_file_path,
                                response=error_response)
            elif response.status_code == 403:
                logger.error("Failed to write to repository - Permission denied",
                            repo_url=repo_url,
                            file=file_path,
                            branch=branch,
                            status_code=response.status_code,
                            error_message=error_message,
                            hint="Token needs 'repo' scope with write permissions")
            else:
                logger.error("Failed to write to repository",
                            repo_url=repo_url,
                            file=file_path,
                            branch=branch,
                            status_code=response.status_code,
                            api_url=api_url,
                            encoded_path=encoded_file_path,
                            response=error_response)
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

