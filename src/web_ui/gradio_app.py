"""Gradio web UI for Moxi - Easy setup interface."""

import gradio as gr
from typing import List, Optional

from core import get_logger
from web_ui.github_client import GitHubClient
from web_ui.workflow_generator import write_workflow_to_repo

logger = get_logger(__name__)

# Store selected repos in session state
selected_repos = {}


def fetch_repos(github_token: str, username: Optional[str] = None) -> tuple[str, List[tuple]]:
    """
    Fetch repositories for a user.
    
    Args:
        github_token: GitHub personal access token
        username: Optional GitHub username (if None, uses authenticated user)
        
    Returns:
        Tuple of (status_message, list of (label, value) tuples for CheckboxGroup)
    """
    if not github_token or not github_token.strip():
        return "❌ Please enter your GitHub token", gr.update(choices=[], value=[])
    
    try:
        client = GitHubClient(github_token)
        
        # Test token
        if not client.test_token():
            return "❌ Invalid GitHub token. Please check your token.", gr.update(choices=[], value=[])
        
        # Get authenticated user if username not provided
        if not username:
            username = client.get_authenticated_user()
            if not username:
                return "❌ Failed to get authenticated user. Please provide username.", gr.update(choices=[], value=[])
        
        # Fetch repositories
        repos = client.get_user_repos(username)
        
        if not repos:
            return f"❌ No repositories found for {username}", gr.update(choices=[], value=[])
        
        # Format for Gradio CheckboxGroup
        # CheckboxGroup expects a list of (label, value) tuples
        # When user selects, it returns a list of selected values (URLs)
        repo_choices = [
            (f"{repo['full_name']} {'🔒' if repo['private'] else '🌐'}", repo['html_url'])
            for repo in repos
        ]
        
        status = f"✅ Found {len(repos)} repositories for {username}\nSelect repositories below to enable auto-documentation."
        logger.info("Fetched repositories", count=len(repos), username=username)
        
        # Return status and update CheckboxGroup choices using gr.update()
        # In Gradio, we need to use gr.update() to update component properties
        return status, gr.update(choices=repo_choices, value=[])
        
    except Exception as e:
        logger.error("Error fetching repositories", error=str(e))
        return f"❌ Error: {str(e)}", gr.update(choices=[], value=[])


def setup_workflows(github_token: str, selected_repo_urls: List[str]) -> str:
    """
    Set up workflows for selected repositories.
    
    Args:
        github_token: GitHub personal access token
        selected_repo_urls: List of selected repository URLs (from CheckboxGroup)
                           Gradio CheckboxGroup with (label, value) tuples returns
                           a list of selected values (the second element of each tuple)
        
    Returns:
        Status message
    """
    if not github_token or not github_token.strip():
        return "❌ Please enter your GitHub token"
    
    if not selected_repo_urls:
        return "❌ Please select at least one repository"
    
    # Gradio CheckboxGroup with (label, value) format returns list of selected values (URLs)
    # But sometimes it might return the full tuple, so we need to handle both cases
    repo_urls = []
    for item in selected_repo_urls:
        if isinstance(item, str):
            # Should be a URL
            if item.startswith("http"):
                repo_urls.append(item)
            elif "/" in item and not item.startswith("http"):
                # Might be a repo name like "LC0229/moxi 🌐"
                # Try to construct URL (but this shouldn't happen with proper format)
                logger.warning("Received repo name instead of URL, skipping", item=item)
            else:
                logger.warning("Unexpected item format", item=item)
        elif isinstance(item, (list, tuple)):
            # If it's a tuple/list, extract the URL (second element)
            if len(item) >= 2:
                url = item[1] if isinstance(item[1], str) else str(item[1])
                if url.startswith("http"):
                    repo_urls.append(url)
        else:
            logger.warning("Unexpected item type", item=item, type=type(item))
    
    if not repo_urls:
        return "❌ No valid repository URLs found. Please:\n1. Click 'Fetch Repositories' first\n2. Select repositories from the list\n3. Then click 'Setup Workflows'"
    
    results = []
    successful = 0
    failed = 0
    
    for repo_url in repo_urls:
        success, message = write_workflow_to_repo(
            repo_url=repo_url,
            github_token=github_token,
        )
        
        if success:
            successful += 1
            results.append(f"✅ {repo_url}")
        else:
            failed += 1
            results.append(f"❌ {repo_url}: {message}")
    
    summary = f"\n\n📊 Summary: {successful} successful, {failed} failed"
    return "\n".join(results) + summary


def create_gradio_interface():
    """Create and return Gradio interface."""
    
    with gr.Blocks(title="Moxi - Auto Documentation Setup") as app:
        gr.Markdown(
            """
            # 🤖 Moxi - Auto Documentation Setup
            
            **One-click setup for automatic README generation on every push!**
            
            ## How it works:
            1. Enter your GitHub token (with `repo` scope)
            2. Optionally enter your GitHub username (or leave blank to use authenticated user)
            3. Click "Fetch Repositories" to see all your repos
            4. Select the repositories you want to enable auto-documentation
            5. Click "Setup Workflows" to automatically add GitHub Actions workflows
            6. Done! Every time you push code, ARCHITECTURE_BY_MOXI.md will be automatically updated
            
            ## Requirements:
            - GitHub Personal Access Token with `repo` scope
            - OpenAI API Key (set as secret `OPENAI_API_KEY` in each repository)
            - Python 3.11+ repositories (or we'll install Python in the workflow)
            
            ## Get your GitHub token:
            Go to: https://github.com/settings/tokens → Generate new token (classic) → Select `repo` scope
            """
        )
        
        with gr.Row():
            with gr.Column(scale=1):
                github_token = gr.Textbox(
                    label="GitHub Personal Access Token",
                    placeholder="ghp_xxxxxxxxxxxx",
                    type="password",
                    info="Token with 'repo' scope required",
                )
                username = gr.Textbox(
                    label="GitHub Username (Optional)",
                    placeholder="Leave blank to use authenticated user",
                    info="If blank, uses the authenticated user from token",
                )
                fetch_btn = gr.Button("Fetch Repositories", variant="primary")
                status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=2,
                )
            
            with gr.Column(scale=2):
                repo_checkboxes = gr.CheckboxGroup(
                    label="Select Repositories",
                    choices=[],
                    info="Select repositories to enable auto-documentation",
                )
                setup_btn = gr.Button("Setup Workflows (One-Click)", variant="primary", size="lg")
                results = gr.Textbox(
                    label="Setup Results",
                    interactive=False,
                    lines=10,
                )
        
        # Event handlers
        fetch_btn.click(
            fn=fetch_repos,
            inputs=[github_token, username],
            outputs=[status, repo_checkboxes],
        )
        
        setup_btn.click(
            fn=setup_workflows,
            inputs=[github_token, repo_checkboxes],
            outputs=[results],
        )
        
        gr.Markdown(
            """
            ---
            ## 📝 Notes:
            - The workflow will generate `ARCHITECTURE_BY_MOXI.md` (architecture diagram, not README)
            - Make sure to add `OPENAI_API_KEY` as a secret in each repository's settings
            - The workflow triggers on pushes to `main`/`master` branches when code files change
            - You can manually trigger the workflow from the Actions tab
            """
        )
    
    return app


def main():
    """Main entry point for Gradio app."""
    import socket
    
    def find_free_port(start_port=7860, max_attempts=10):
        """Find a free port starting from start_port."""
        for i in range(max_attempts):
            port = start_port + i
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        return None  # Fallback to let Gradio find a port
    
    app = create_gradio_interface()
    port = find_free_port(7860) or 0  # 0 means let Gradio find a port automatically
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,  # Set to True to create a public link
        # Note: theme parameter is not available in Gradio 4.x launch()
        # To use themes in Gradio 4.x, set it when creating Blocks: gr.Blocks(theme=gr.themes.Soft())
    )


if __name__ == "__main__":
    main()

