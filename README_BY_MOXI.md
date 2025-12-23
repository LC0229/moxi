# moxi
Last updated: 2025-12-23 10:36:09 UTC

moxi is an AI-powered documentation generator that automates the creation and updating of documentation based on changes in your codebase.

## How This Project Works

The moxi library is designed to facilitate the generation and maintenance of documentation using AI. The architecture consists of several key components:

1. **Input Sources**: moxi analyzes the structure of your repository through various crawlers located in the `repo_analyzer` module. This can include both local and remote repositories, such as GitHub.

2. **Data Processing**: Once the repository structure is analyzed, the `dataset_generator` component generates datasets that provide context and structure for documentation. This involves web scraping through crawlers and utilizing instruction generators.

3. **Documentation Generation**: The `doc_generator` module utilizes the OpenAI API to generate documentation based on the analyzed data and datasets. It uses language models to create coherent and contextually relevant documentation.

4. **Quality Control**: The library includes quality control mechanisms to ensure the generated documentation is accurate and free from duplicates.

5. **Auto-update Mechanism**: The integration with GitHub Actions allows for automatic commits and pushes of the generated documentation whenever code changes are made to the repository.

The data flow can be summarized as follows:
- **Input**: Codebase changes → Repository analysis → Dataset generation
- **Processing**: Data is analyzed and structured → Documentation is generated using AI
- **Output**: Updated documentation is committed back to the repository

## How to Use

### Step-by-Step Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/moxi.git
   cd moxi
   ```

2. **Set Up Environment**:
   Create a `.env` file based on `.env.example` and add your OpenAI API key:
   ```bash
   cp .env.example .env
   ```

3. **Install Dependencies**:
   Use Poetry to install the required dependencies:
   ```bash
   poetry install
   ```

4. **Run the Documentation Generator**:
   Execute the main script for documentation generation:
   ```bash
   poetry run python src/doc_generator/main.py
   ```

### Command-line Examples
- To analyze a local repository:
  ```bash
  poetry run python src/repo_analyzer/main.py --path /path/to/local/repo
  ```

- To generate documentation:
  ```bash
  poetry run python src/doc_generator/main.py --output README_BY_MOXI.md
  ```

### Configuration Options
- You can configure the output file and the repository path via command-line arguments.

### Common Use Cases
- Continuous documentation updates for large codebases.
- Documentation generation for open-source projects hosted on GitHub.

## Features
- Automatic documentation generation using AI.
- Supports local and GitHub repository analysis.
- Quality control for generated documentation.
- Integration with GitHub Actions for automated updates.
- Customizable through command-line parameters.

## Installation Instructions

To install moxi, clone the repository and install the dependencies using Poetry:

```bash
git clone https://github.com/yourusername/moxi.git
cd moxi
poetry install
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
│   │   │   └── instruction_gen.py
│   │   ├── main.py
│   │   ├── quality_control/
│   │   │   ├── __init__.py
│   │   │   ├── deduplicator.py
│   │   │   └── validator.py
│   │   └── utils.py
│   ├── doc_generator/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├──