"""Generate and write GitHub Actions workflow files."""

from typing import Optional

import requests

from core import get_logger
from core.lib import extract_repo_owner_and_name
from doc_generator.writer import write_to_repo_via_api

logger = get_logger(__name__)

# GitHub Actions workflow template
WORKFLOW_TEMPLATE = """name: Auto-generate Documentation

on:
  push:
    branches:
      - main
      - master
    paths:
      # Only trigger when code changes, not when README changes
      - 'src/**'
      - '**/*.py'  # Python files anywhere in the repo
      - 'pyproject.toml'
      - '.github/workflows/auto-generate-docs.yml'
      - 'Makefile'
      - 'package.json'
      - 'requirements.txt'
      - 'setup.py'
      - 'Cargo.toml'
      - 'go.mod'
  workflow_dispatch:  # Allow manual trigger

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    
    permissions:
      contents: write  # Required to write files to repository
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          # Note: cache is optional and requires requirements.txt or pyproject.toml
          # If the repo doesn't have these files, remove the cache line
          # cache: 'pip'  # Commented out to work with repos without dependency files
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pydantic pydantic-settings structlog rich click requests openai tomli
      
      - name: Configure environment
        run: |
          touch .env
      
      - name: Generate documentation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Clone moxi repository to get the doc_generator module
          echo "Cloning moxi repository..."
          git clone --depth 1 https://github.com/LC0229/moxi.git /tmp/moxi
          export PYTHONPATH=/tmp/moxi/src:$PYTHONPATH
          cd /tmp/moxi/src
          python -m doc_generator.main \\
            https://github.com/${{ github.repository }} \\
            --auto-write \\
            --file-name README_BY_MOXI.md
"""


def generate_workflow_content() -> str:
    """
    Generate GitHub Actions workflow content.
    
    Returns:
        Workflow YAML content as string
    """
    return WORKFLOW_TEMPLATE


def write_workflow_to_repo(
    repo_url: str,
    github_token: str,
    branch: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Write GitHub Actions workflow file to a repository.
    
    Args:
        repo_url: GitHub repository URL (e.g., "https://github.com/user/repo")
        github_token: GitHub personal access token
        branch: Branch name (if None, uses default branch)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Get default branch if not provided
        if branch is None:
            owner, repo = extract_repo_owner_and_name(repo_url)
            if owner and repo:
                # Get repository info to find default branch
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                headers = {
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json",
                }
                response = requests.get(api_url, headers=headers)
                if response.status_code == 200:
                    branch = response.json().get("default_branch", "main")
                    logger.info("Detected default branch", repo=repo_url, branch=branch)
                else:
                    branch = "main"  # Fallback
                    logger.warning("Failed to get default branch, using 'main'", repo=repo_url)
            else:
                branch = "main"  # Fallback
                logger.warning("Invalid repo URL, using 'main'", repo=repo_url)
        
        # Generate workflow content
        workflow_content = generate_workflow_content()
        
        # Workflow file path
        workflow_path = ".github/workflows/auto-generate-docs.yml"
        
        # Write workflow file
        success = write_to_repo_via_api(
            repo_url=repo_url,
            content=workflow_content,
            file_path=workflow_path,
            branch=branch,
            commit_message="ci: Add Moxi auto-documentation workflow",
            github_token=github_token,
        )
        
        if success:
            logger.info("Successfully wrote workflow", repo_url=repo_url, workflow_path=workflow_path)
            return True, f"✅ Successfully set up workflow for {repo_url}"
        else:
            logger.error("Failed to write workflow", repo_url=repo_url)
            return False, f"❌ Failed to write workflow to {repo_url}\n💡 Tip: Make sure your GitHub token has 'repo' scope (not just 'public_repo'). Go to GitHub Settings → Developer settings → Personal access tokens → Edit token → Select 'repo' scope."
            
    except Exception as e:
        logger.error("Error writing workflow", repo_url=repo_url, error=str(e))
        return False, f"❌ Error: {str(e)}"

