"""
Gradio UI for manual repository review.

This UI allows users to:
1. View repository structure
2. See file tree
3. Mark repositories as Keep or Discard
4. Navigate through candidate repositories
"""

import gradio as gr
from typing import Optional

from core import get_logger
from moxi_data.review_backend import RepositoryReviewer

logger = get_logger(__name__)


class ReviewUI:
    """Gradio UI for repository review."""
    
    def __init__(self, reviewer: RepositoryReviewer):
        self.reviewer = reviewer
        self.current_repos = []
        self.current_index = 0
        
    def load_repos(self, source: str, min_stars: int, limit: int, progress=gr.Progress()):
        """Load candidate repositories."""
        try:
            progress(0, desc="Fetching repositories from GitHub...")
            
            # This will take time - show progress
            self.current_repos = self.reviewer.get_candidate_repos(
                source=source,
                min_stars=min_stars,
                limit=limit
            )
            
            progress(1.0, desc="Loading complete!")
            self.current_index = 0
            
            if not self.current_repos:
                return "No candidate repositories found. Try different parameters.", None, None, None, None
            
            return self._show_current_repo()
        except Exception as e:
            logger.error("Error loading repos", error=str(e))
            return f"Error: {str(e)}", None, None, None, None
    
    def _show_current_repo(self):
        """Show current repository."""
        if not self.current_repos or self.current_index >= len(self.current_repos):
            return "No more repositories to review.", None, None, None, None
        
        repo_url = self.current_repos[self.current_index]
        repo_info = self.reviewer.get_repo_info(repo_url)
        
        if not repo_info:
            return f"Error loading repository: {repo_url}", None, None, None, None
        
        # Format display
        status = f"Repository {self.current_index + 1} / {len(self.current_repos)}"
        
        info_text = f"""
**Repository URL:** {repo_info['url']}

**Project Type:** {repo_info['project_type']}
**Language:** {repo_info['project_language']}

**Structure Analysis:**
- Frontend: {'✅' if repo_info['structure']['has_frontend'] else '❌'}
- Backend: {'✅' if repo_info['structure']['has_backend'] else '❌'}
- Server/API: {'✅' if repo_info['structure']['has_server'] or repo_info['structure']['has_api'] else '❌'}
- Database: {'✅' if repo_info['structure']['has_database'] else '❌'}
- Docker: {'✅' if repo_info['structure']['has_docker'] else '❌'}
- Kubernetes: {'✅' if repo_info['structure']['has_k8s'] else '❌'}

**Code Statistics:**
- Code Files: {repo_info['structure']['code_file_count']}
- Code Directories: {repo_info['structure']['code_dirs']}
- Top-level Directories: {', '.join(repo_info['structure']['top_level_dirs'][:10])}

**Key Files:**
{chr(10).join(f"- {k}: {v}" for k, v in list(repo_info['key_files'].items())[:10])}
"""
        
        file_tree = repo_info['file_tree']
        
        return status, info_text, file_tree, repo_url, f"{self.current_index + 1}/{len(self.current_repos)}"
    
    def mark_keep(self, repo_url: str):
        """Mark repository as kept."""
        if repo_url:
            self.reviewer.mark_repo(repo_url, "keep")
            self.current_index += 1
            return self._show_current_repo()
        return "No repository selected", None, None, None, None
    
    def mark_discard(self, repo_url: str):
        """Mark repository as discarded."""
        if repo_url:
            self.reviewer.mark_repo(repo_url, "discard")
            self.current_index += 1
            return self._show_current_repo()
        return "No repository selected", None, None, None, None
    
    def next_repo(self):
        """Move to next repository."""
        self.current_index += 1
        return self._show_current_repo()
    
    def prev_repo(self):
        """Move to previous repository."""
        if self.current_index > 0:
            self.current_index -= 1
        return self._show_current_repo()
    
    def get_kept_repos_list(self):
        """Get list of kept repositories for display."""
        kept_repos = self.reviewer.get_kept_repos()
        if not kept_repos:
            return "**No repositories kept yet.**\n\nClick 'Keep' on repositories in the Review tab to add them here.", gr.update(choices=[], value=None)
        
        # Format as numbered list with markdown
        repo_list = "\n".join([f"{i+1}. `{repo}`" for i, repo in enumerate(kept_repos)])
        count_text = f"**Total: {len(kept_repos)} repositories**\n\n"
        
        # Create choices for dropdown (for removal)
        choices = kept_repos.copy()
        
        return count_text + repo_list, gr.update(choices=choices, value=choices[0] if choices else None)
    
    def remove_kept_repo(self, selected_repo: str):
        """Remove a repository from kept list."""
        if not selected_repo:
            kept_repos = self.reviewer.get_kept_repos()
            return "Please select a repository to remove.", gr.update(choices=kept_repos, value=None)
        
        success = self.reviewer.remove_from_kept(selected_repo)
        if success:
            # Refresh the list after removal
            kept_repos = self.reviewer.get_kept_repos()
            if not kept_repos:
                return "**Repository removed!**\n\n**No repositories kept yet.**", gr.update(choices=[], value=None)
            
            repo_list = "\n".join([f"{i+1}. `{repo}`" for i, repo in enumerate(kept_repos)])
            count_text = f"**Total: {len(kept_repos)} repositories**\n\n✅ Removed: `{selected_repo}`\n\n"
            return count_text + repo_list, gr.update(choices=kept_repos, value=kept_repos[0] if kept_repos else None)
        else:
            kept_repos = self.reviewer.get_kept_repos()
            return f"❌ Repository not found in kept list: `{selected_repo}`", gr.update(choices=kept_repos, value=None)
    
    def create_ui(self):
        """Create Gradio interface."""
        with gr.Blocks(title="Repository Reviewer") as app:
            gr.Markdown("# 🔍 Repository Reviewer")
            gr.Markdown("Review and mark repositories for dataset generation")
            
            # Create tabs for Review and Kept Repos
            with gr.Tabs():
                # Tab 1: Review Repositories
                with gr.Tab("📋 Review Repositories"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            source = gr.Radio(
                                choices=["github", "well_structured"],
                                value="github",
                                label="Source"
                            )
                            min_stars = gr.Number(
                                value=10,
                                label="Min Stars",
                                precision=0
                            )
                            limit = gr.Number(
                                value=50,
                                label="Limit",
                                precision=0
                            )
                            load_btn = gr.Button("Load Repositories", variant="primary")
                        
                        with gr.Column(scale=2):
                            status = gr.Textbox(label="Status", interactive=False)
                            progress = gr.Textbox(label="Progress", interactive=False)
                    
                    with gr.Row():
                        with gr.Column():
                            repo_info = gr.Markdown(label="Repository Information")
                            file_tree = gr.Textbox(
                                label="File Tree",
                                lines=20,
                                max_lines=30
                            )
                            repo_url_hidden = gr.Textbox(visible=False)
                        
                    with gr.Row():
                        prev_btn = gr.Button("← Previous")
                        keep_btn = gr.Button("✅ Keep", variant="primary")
                        discard_btn = gr.Button("❌ Discard", variant="stop")
                        next_btn = gr.Button("Next →")
                
                # Tab 2: Kept Repositories
                with gr.Tab("✅ Kept Repositories"):
                    gr.Markdown("### Repositories you've approved for dataset generation")
                    
                    with gr.Row():
                        with gr.Column(scale=3):
                            kept_repos_display = gr.Markdown(
                                label="Kept Repositories",
                                value="Loading..."
                            )
                        
                        with gr.Column(scale=1):
                            refresh_btn = gr.Button("🔄 Refresh List", variant="secondary")
                            gr.Markdown("---")
                            gr.Markdown("### Remove Repository")
                            gr.Markdown("Select a repository to remove if you accidentally clicked Keep:")
                            
                            kept_repos_dropdown = gr.Dropdown(
                                label="Select Repository to Remove",
                                choices=[],
                                interactive=True
                            )
                            remove_btn = gr.Button("🗑️ Remove from Kept", variant="stop")
                    
                    # Event handlers for Kept Repos tab
                    refresh_btn.click(
                        fn=self.get_kept_repos_list,
                        inputs=[],
                        outputs=[kept_repos_display, kept_repos_dropdown]
                    )
                    
                    remove_btn.click(
                        fn=self.remove_kept_repo,
                        inputs=[kept_repos_dropdown],
                        outputs=[kept_repos_display, kept_repos_dropdown]
                    )
                    
                    # Load kept repos on tab open
                    app.load(
                        fn=self.get_kept_repos_list,
                        inputs=[],
                        outputs=[kept_repos_display, kept_repos_dropdown]
                    )
            
            # Event handlers for Review tab
            load_btn.click(
                fn=self.load_repos,
                inputs=[source, min_stars, limit],
                outputs=[status, repo_info, file_tree, repo_url_hidden, progress],
                show_progress=True
            )
            
            keep_btn.click(
                fn=self.mark_keep,
                inputs=[repo_url_hidden],
                outputs=[status, repo_info, file_tree, repo_url_hidden, progress]
            )
            
            discard_btn.click(
                fn=self.mark_discard,
                inputs=[repo_url_hidden],
                outputs=[status, repo_info, file_tree, repo_url_hidden, progress]
            )
            
            next_btn.click(
                fn=self.next_repo,
                inputs=[],
                outputs=[status, repo_info, file_tree, repo_url_hidden, progress]
            )
            
            prev_btn.click(
                fn=self.prev_repo,
                inputs=[],
                outputs=[status, repo_info, file_tree, repo_url_hidden, progress]
            )
        
        return app


def main():
    """Launch review UI."""
    reviewer = RepositoryReviewer()
    ui = ReviewUI(reviewer)
    app = ui.create_ui()
    
    # Find free port
    import socket
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]
    
    port = find_free_port()
    app.launch(server_name="0.0.0.0", server_port=port, share=False)
    print(f"\n✅ Review UI launched on http://localhost:{port}")


if __name__ == "__main__":
    main()

