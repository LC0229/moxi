"""Web UI module for Moxi - Gradio frontend for easy setup."""

from .github_client import GitHubClient
from .workflow_generator import generate_workflow_content, write_workflow_to_repo

__all__ = [
    "GitHubClient",
    "generate_workflow_content",
    "write_workflow_to_repo",
]

