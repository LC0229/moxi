# moxi  
Last updated: 2026-01-03 04:43:53 UTC

## Project Description
moxi is an AI-powered documentation generator that automatically generates and updates documentation based on your codebase. It leverages advanced language models to analyze your repository and produce comprehensive documentation, ensuring that it remains up-to-date with the latest changes.

## How This Project Works
moxi follows a modular architecture consisting of several components that interact seamlessly to generate documentation:

1. **Core Module**: This is the backbone of the application, containing utilities for configuration management, logging, and message queuing.
2. **Dataset Generator**: Responsible for creating datasets by crawling various sources (e.g., GitHub trends, awesome lists) and generating instructional content.
3. **Repository Analyzer**: This component analyzes the code repository, extracting necessary information such as file structure and code definitions.
4. **Documentation Generator**: Utilizes a language model (e.g., GPT-4o-mini) to create documentation based on the analysis performed by the Repository Analyzer.
5. **Training Pipeline**: This module focuses on fine-tuning models and managing training workflows, ensuring that the documentation generation process is optimized.
6. **Web UI**: Provides a user-friendly interface for interacting with the moxi library, including features for workflow generation and GitHub integration.

The data flow is as follows:
1. The user triggers the documentation generation process, either automatically via GitHub Actions or manually through the command line.
2. The Repository Analyzer scans the repository and collects relevant information.
3. The Dataset Generator compiles datasets based on the gathered information.
4. The Documentation Generator produces the documentation, which is then committed back to the repository.

## How to Use
Follow these steps to get started with moxi:

1. **Install the Required Dependencies**:
   Ensure you have Python 3.11 or greater installed. Use the `pyproject.toml` file for dependency management with Poetry:
   ```bash
   poetry install
   ```

2. **Configure Your Environment**:
   Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Fill in the required environment variables, including your OpenAI API key.

3. **Run the Documentation Generation**:
   You can run the documentation generation process via command line. Navigate to the `src/doc_generator` directory and execute:
   ```bash
   python main.py
   ```

4. **Using the CLI**:
   You can also utilize the command-line interface provided in the `cli` module:
   ```bash
   python -m cli <command>
   ```

### Configuration Options
- **OPENAI_API_KEY**: Your OpenAI API key for generating documentation.
- Additional configuration options can be specified in the `.env` file.

### Common Use Cases
- Automatically generate documentation after code changes.
- Generate instructional content for new features.
- Maintain updated documentation without manual intervention.

## Features
- **AI-Powered**: Uses advanced language models to generate human-like documentation.
- **Automatic Updates**: Automatically updates documentation on code changes via GitHub Actions.
- **Modular Design**: Each component can be developed and tested independently.
- **Web UI**: Offers an intuitive interface for users to interact with the library.
- **Versatile Dataset Generation**: Capable of crawling various sources for dataset creation.

## Installation Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/moxi.git
   cd moxi
   ```
   
2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Set up environment variables as mentioned in the "How to Use" section.

## Usage Examples
To generate documentation for your project, execute:
```bash
python src/doc_generator/main.py
```
You can also trigger the documentation generation workflow manually from the GitHub Actions tab.

## Project Structure
```
├── .env.example
├── Makefile
├── README.md
├── README_BY_MOXI.md
├── docker-compose.yml
├── poetry.lock
├── pyproject.toml
├── src/
│   ├── cli/
│   │   └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── qdrant.py
│   │   ├── errors.py
│   │   ├── lib.py
│   │   ├── logger_utils.py
│   │   └── mq.py
│   ├── dataset_generator/
│   │   ├── __init__.py
│   │   ├── core.py
│