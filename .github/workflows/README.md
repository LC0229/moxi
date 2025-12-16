# GitHub Actions Workflows

## Auto-generate Documentation

This workflow automatically generates and updates `README_BY_MOXI.md` whenever code changes are pushed to the repository.

### Setup

1. **Add Secrets to GitHub Repository:**
   - Go to Settings → Secrets and variables → Actions
   - Add `OPENAI_API_KEY`: Your OpenAI API key for generating documentation
   - `GITHUB_TOKEN` is automatically provided by GitHub Actions

2. **Workflow Triggers:**
   - Automatically runs on push to `main` or `master` branch
   - Only triggers when code files change (not when README changes)
   - Can be manually triggered from Actions tab

3. **What it does:**
   - Analyzes the repository structure
   - Generates documentation using GPT-4o-mini
   - Automatically commits and pushes `README_BY_MOXI.md`

### Manual Trigger

You can manually trigger this workflow:
1. Go to Actions tab in GitHub
2. Select "Auto-generate Documentation"
3. Click "Run workflow"

