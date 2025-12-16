# Moxi

**AI-Powered Documentation Generator with Continuous Learning**

Moxi is an intelligent documentation generator that analyzes GitHub repositories and creates high-quality, comprehensive documentation using fine-tuned Large Language Models. Moxi implements a complete ML pipeline from data collection to model deployment, with automatic documentation updates on every code push.

---

## Key Features

- **Custom Fine-Tuned Model**: Train your own Llama-3.1-8B specialized for documentation.
- **Automated Dataset Generation**: Create training data from 10,000+ GitHub repositories.
- **Intelligent Repository Analysis**: Parse and understand project structures.
- **Multi-Format Documentation**: Generate README, ARCHITECTURE, and API docs.
- **A/B Testing**: Compare your model against GPT-4.
- **Docker Ready**: Easy deployment with Docker Compose.
- **CLI Tool**: Simple command-line interface for seamless interactions.
- **Auto-Update on Push**: Automatically detect code changes and update documentation.

---

## Installation Instructions

To install Moxi, ensure you have Python 3.11 or higher. You can use [Poetry](https://python-poetry.org/) to manage dependencies and virtual environments.

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/moxi.git
   cd moxi
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. (Optional) Copy the example environment configuration:
   ```bash
   cp .env.example .env
   ```

4. Configure your environment variables in the `.env` file as needed.

5. Run Moxi:
   ```bash
   poetry run python -m src.cli
   ```

---

## Usage Examples

To generate documentation for your project, run the CLI tool with the desired command. Here’s a basic usage example:

```bash
poetry run python -m src.cli generate --repo your_github_repo_url
```

This command analyzes the specified GitHub repository and generates the necessary documentation files.

---

## Project Structure

```
├── .env.example
├── Makefile
├── README.md
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
│   │   └── __init__.py
│   ├── doc_generator/
│   │   └── __init__.py
│   ├── repo_analyzer/
│   │   └── __init__.py
│   ├── training_pipeline/
│   │   └── __init__.py
```

---

## Contributing Guidelines

We welcome contributions to Moxi! If you'd like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with clear messages.
4. Push your branch to your forked repository.
5. Open a pull request describing your changes.

Please ensure your code adheres to the project's style guidelines and includes appropriate tests.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.