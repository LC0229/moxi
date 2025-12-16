# moxi
Last updated: 2025-12-16 13:38:57 UTC

## Description
moxi is an AI-powered documentation generator that automatically updates documentation based on changes in your codebase. It leverages advanced language models to analyze your repository structure and generate comprehensive documentation, ensuring that your docs are always up-to-date.

## How This Project Works
moxi operates through a modular architecture that consists of several components:

1. **Repo Analyzer**: This component crawls the repository, analyzing both local and GitHub-hosted code. It identifies files, directories, and their relationships to understand the overall structure of the project.

2. **Dataset Generator**: This module collects and processes data from various sources, including GitHub trending repositories and curated awesome lists. It generates datasets that are essential for training the AI models used in documentation generation.

3. **Document Generator**: This core component utilizes the collected datasets and AI models (such as GPT-4o-mini) to create documentation. It processes the information and generates human-readable files, including the `README_BY_MOXI.md`, which is automatically updated with relevant changes.

4. **Training Pipeline**: moxi includes a training pipeline that allows for fine-tuning AI models based on custom datasets. This ensures that the documentation remains relevant and tailored to the specific needs of the repository.

The overall workflow is as follows:
- When code changes are pushed to the repository, the Auto-generate Documentation workflow is triggered.
- The Repo Analyzer scans the codebase, and the Dataset Generator prepares the necessary data.
- The Document Generator processes this information and updates the documentation files.
- The updated documentation is then committed back to the repository.

## How to Use
1. **Installation**: 
   To get started with moxi, clone the repository and install the dependencies:

   ```bash
   git clone <repository-url>
   cd moxi
   poetry install
   ```

2. **Configuration**:
   Set up the necessary environment variables by copying the `.env.example` file and filling in your `OPENAI_API_KEY`.
   
   ```bash
   cp .env.example .env
   ```

3. **Running the Documentation Generator**:
   You can generate documentation manually by running the following command:

   ```bash
   python src/doc_generator/main.py
   ```

4. **Workflow Triggers**:
   - The documentation auto-generates on pushes to the `main` or `master` branches.
   - You can also manually trigger the workflow from the GitHub Actions tab.

### Command-Line Examples
To run the dataset generator:
```bash
python src/dataset_generator/main.py
```

To analyze a specific repository:
```bash
python src/repo_analyzer/main.py --repo <repository-url>
```

## Features
- **AI-Powered**: Utilizes advanced AI models to generate human-friendly documentation.
- **Auto-Update**: Automatically updates documentation based on code changes.
- **Modular Architecture**: Components can be independently developed and tested.
- **Custom Training**: Allows for fine-tuning models based on specific datasets.
- **Cross-Platform**: Works seamlessly with both local and GitHub-hosted repositories.

## Installation Instructions
1. Ensure Python 3.11 or higher is installed on your machine.
2. Clone the repository:
   ```bash
   git clone <repository-url>
   cd moxi
   ```
3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

## Usage Examples
For generating documentation, simply run:
```bash
python src/doc_generator/main.py
```
This will analyze the current repository and produce an updated `README_BY_MOXI.md` file.

To generate datasets from trending repositories:
```bash
python src/dataset_generator/main.py
```

## Project Structure
```
├── .env.example
├── Makefile
├── README.md
├── README_BY_MOXI.md
├── poetry.lock
├── pyproject.toml
├── src/
│   ├── cli/
│   │   └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── errors.py
│   │   ├── lib.py
│   │   └── logger_utils.py
│   ├── dataset_generator/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── crawlers/
│   │   │   ├── __init__.py
│   │   │   ├── awesome_lists.py
│   │   │   └── github_trending.py
│   │   ├── generators/
│   │   │   ├── __init__.py
│   │   │   └── instruction