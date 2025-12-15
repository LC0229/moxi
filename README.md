# Moxi 🚀

**AI-Powered Documentation Generator with Continuous Learning**

Moxi is an intelligent documentation generator that analyzes GitHub repositories and creates high-quality, comprehensive documentation using fine-tuned Large Language Models. Inspired by [llm-twin-course](https://github.com/decodingml/llm-twin-course), Moxi implements a complete ML pipeline from data collection to model deployment.

---

## 🎯 What Does Moxi Do?

Moxi automates the tedious process of writing documentation by:
1. **Analyzing** your codebase structure and key files
2. **Understanding** your project's architecture and purpose
3. **Generating** professional README files, architecture docs, and API documentation
4. **Learning** from thousands of high-quality open-source projects

---

## ✨ Key Features

- 🤖 **Custom Fine-Tuned Model** - Train your own Llama-3.1-8B specialized for documentation
- 📊 **Automated Dataset Generation** - Create training data from 10,000+ GitHub repositories
- 🔍 **Intelligent Repository Analysis** - Parse and understand project structures
- 📝 **Multi-Format Documentation** - Generate README, ARCHITECTURE, API docs
- 🎯 **A/B Testing** - Compare your model against GPT-4
- 🐳 **Docker Ready** - Easy deployment with Docker Compose
- 🛠️ **CLI Tool** - Simple command-line interface

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MOXI PIPELINE                            │
└─────────────────────────────────────────────────────────────┘

1️⃣  REPO ANALYZER
    ├── GitHub Crawler
    ├── Structure Parser
    └── File Analyzer
    
2️⃣  DATASET GENERATOR
    ├── GitHub Trending Crawler
    ├── Instruction Generator (GPT-4)
    └── Quality Control
    
3️⃣  TRAINING PIPELINE
    ├── SFT Trainer (LoRA/QLoRA)
    ├── Experiment Tracking (W&B)
    └── Model Evaluation
    
4️⃣  DOC GENERATOR
    ├── Custom Model Inference
    ├── Format & Validate
    └── Export Markdown
    
5️⃣  CLI & EVALUATION
    ├── Command-Line Interface
    └── A/B Testing Framework
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API Key (for dataset generation)
- Hugging Face Token (for model training)
- GitHub Token (for repo crawling)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/moxi.git
cd moxi

# Create virtual environment
python -m venv moxi
source moxi/bin/activate  # On Windows: moxi\Scripts\activate

# Install dependencies
make install

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

```bash
# Test configuration
make test-config

# Analyze a repository
make local-analyze-repo REPO=https://github.com/pytorch/pytorch

# Generate documentation (using pre-trained model)
make local-generate-docs REPO=https://github.com/pytorch/pytorch
```

---

## 📚 Full Pipeline

### Step 1: Generate Training Dataset

```bash
# Crawl 100+ high-quality GitHub repositories
make crawl-github-repos

# Generate 10,000 training samples using GPT-4
make generate-training-dataset

# Validate dataset quality
make validate-dataset
```

**Cost:** ~$20-30 in OpenAI API credits

### Step 2: Train Your Model

```bash
# Download base Llama-3.1-8B model
make download-base-model

# Train with Supervised Fine-Tuning (SFT)
make train-sft

# Evaluate model performance
make evaluate-model
```

**Time:** 4-8 hours on GPU (AWS g5.2xlarge recommended)

### Step 3: Generate Documentation

```bash
# Use your trained model
make local-generate-docs REPO=https://github.com/user/repo

# Compare with GPT-4 baseline
make compare-models
```

---

## 🛠️ Development

### Project Structure

```
moxi/
├── src/
│   ├── core/               # Configuration, logging, utilities
│   ├── repo_analyzer/      # GitHub crawler & parser
│   ├── dataset_generator/  # Training data creation
│   ├── training_pipeline/  # Model training & evaluation
│   ├── doc_generator/      # Documentation generation
│   └── cli/                # Command-line interface
├── tests/
│   ├── unit/
│   └── integration/
├── data/                   # Downloaded repositories
├── training_data/          # Generated datasets
├── models/                 # Trained models
└── Makefile               # All commands
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test suites
make test-unit
make test-integration
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format
```

---

## 📊 Dataset & Training

### Dataset Statistics

- **Source:** GitHub repositories (100+ stars)
- **Size:** 10,000+ instruction-output pairs
- **Format:** JSON with instruction, input, output fields
- **Quality:** Validated by GPT-4 + human review

### Training Configuration

- **Base Model:** Meta Llama-3.1-8B-Instruct
- **Method:** Supervised Fine-Tuning (SFT) with LoRA
- **Hyperparameters:**
  - Learning Rate: 2e-4
  - Batch Size: 4 (per device)
  - Gradient Accumulation: 4 steps
  - Epochs: 3
  - Max Sequence Length: 2048 tokens

### Hardware Requirements

- **Training:** GPU with 16GB+ VRAM (NVIDIA A10G, V100, or better)
- **Inference:** GPU with 8GB+ VRAM or CPU (slower)

---

## 🐳 Docker Deployment

```bash
# Build containers
make docker-build

# Start services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

---

## 📖 CLI Usage

```bash
# Generate documentation
python -m cli.main generate https://github.com/user/repo

# Analyze repository structure
python -m cli.main analyze https://github.com/user/repo

# Evaluate model performance
python -m cli.main evaluate --compare custom vs gpt4
```

---

## 🎯 Roadmap

- [x] Phase 0: Project Setup
- [x] Phase 1: Core Infrastructure
- [ ] Phase 2: Repository Analyzer
- [ ] Phase 3: Dataset Generator
- [ ] Phase 4: Training Pipeline
- [ ] Phase 5: Documentation Generator
- [ ] Phase 6: CLI & Evaluation
- [ ] Phase 7: Docker & Deployment
- [ ] Phase 8: Documentation & Demo

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by [llm-twin-course](https://github.com/decodingml/llm-twin-course) by Paul Iusztin
- Built with [Llama-3.1-8B](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)
- Powered by Hugging Face Transformers, PEFT, and TRL

---

## 📧 Contact

- **Author:** Shengrui Chen
- **Email:** chenleon572@gmail.com
- **GitHub:** [@yourusername](https://github.com/yourusername)

---

⭐ **Star this repo if you find it useful!** ⭐

