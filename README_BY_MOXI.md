# Moxi

**AI-Powered Documentation Generator with Continuous Learning**

Moxi is an intelligent documentation generator that analyzes GitHub repositories and creates high-quality, comprehensive documentation using fine-tuned Large Language Models. Moxi implements a complete ML pipeline from data collection to model deployment, with automatic documentation updates on every code push.

---

## Features

- **Custom Fine-Tuned Model**: Train your own Llama-3.1-8B specialized for documentation.
- **Automated Dataset Generation**: Create training data from 10,000+ GitHub repositories.
- **Intelligent Repository Analysis**: Parse and understand project structures.
- **Multi-Format Documentation**: Generate README, ARCHITECTURE, and API documentation.
- **A/B Testing**: Compare your model against GPT-4.
- **Docker Ready**: Easy deployment with Docker Compose.
- **CLI Tool**: Simple command-line interface to interact with Moxi.
- **Auto-Update on Push**: Automatically detect code changes and update documentation.

---

## Installation Instructions

To install Moxi, ensure you have Python 3.11 or higher. You can set up your environment and install the package using Poetry:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/moxi.git
   cd moxi
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Activate the environment:
   ```bash
   poetry shell
   ```

---

## Usage Examples

To generate documentation with Moxi, you would typically run the following command in your terminal:

```bash
moxi generate --path /path/to/your/repo
```

You can also specify options such as the output format and the specific files to analyze. For more detailed usage information, run:

```bash
moxi --help
```

---

## Project Structure

```
moxi/
├── README.md               # Project documentation
├── readme.md              # Alternate README file
├── pyproject.toml         # Project configuration and dependencies
└── package_init/
    └── __init__.py        # Package initialization file
```

---

## Contributing Guidelines

We welcome contributions to Moxi! If you would like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your branch and create a pull request.

Please ensure your code adheres to the project's coding standards and includes appropriate tests.

---

## License

Moxi is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.