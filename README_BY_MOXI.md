# moxi 
Last updated: 2026-01-03 04:42:48 UTC

## Description
moxi is an AI-powered documentation generator that automatically keeps your documentation up-to-date with the latest changes in your codebase. Leveraging advanced AI capabilities, it analyzes the structure of your project and creates comprehensive documentation, which is stored in `README_BY_MOXI.md`.

## How This Project Works
moxi operates through a modular architecture that consists of several components working together seamlessly:

1. **Repository Analyzer**: The `repo_analyzer` module crawls through the project files using the `crawlers`, which include `github.py` and `local.py`, to gather information about the repository structure.

2. **Dataset Generator**: The `dataset_generator` module utilizes crawlers like `awesome_lists.py` and `github_trending.py` to gather data, which is then processed through the `generators` to create instructional datasets.

3. **Document Generator**: The `doc_generator` module uses AI models from the `llm` folder (such as `openai.py`) to generate documentation based on the analyzed data.

4. **Training Pipeline**: The `training_pipeline` contains scripts for fine-tuning models, including `lora_config.py` and `sft_trainer.py`, to enhance the quality of generated documentation.

The workflow is triggered upon pushing changes to the repository, automatically generating and updating the documentation, ensuring that it is always reflective of the current state of the code.

## How to Use
To use moxi effectively, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/moxi.git
   cd moxi
   ```

2. **Set Up Environment**:
   Create a `.env` file based on the `.env.example` provided to configure your environment variables, particularly your OpenAI API key.

3. **Install Dependencies**:
   Ensure you have Python 3.11 or higher installed. Then, install the necessary dependencies using Poetry:
   ```bash
   poetry install
   ```

4. **Run the Documentation Generation**:
   You can run the document generation process via the command line:
   ```bash
   python src/doc_generator/main.py
   ```

5. **Trigger Documentation Update**:
   After making changes to your code, push to `main` or `master` branch to automatically trigger the documentation update.

### Configuration Options
You may customize the documentation generation by altering the configurations in `config.py` located in the `core` directory.

### Common Use Cases
- Automatically generate documentation after each code change.
- Analyze and document complex repository structures.
- Generate instructional materials for new team members or users.

## Features
- AI-powered documentation generation.
- Automatic updates to documentation upon code changes.
- Modular architecture for easy extensibility.
- Supports both local and GitHub repository analysis.
- Fine-tuning capabilities for enhanced documentation quality.

## Installation Instructions
To install moxi, follow these steps:

1. Ensure you have Python 3.11 or higher.
2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/moxi.git
   cd moxi
   ```
3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

## Usage Examples
To generate documentation, simply run:
```bash
python src/doc_generator/main.py
```
To manually trigger documentation generation via GitHub Actions, go to the Actions tab and run the "Auto-generate Documentation" workflow.

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
│   │   │   ├── deduplic