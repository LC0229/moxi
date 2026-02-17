# Moxi

**AI-powered README generator** — collect READMEs from GitHub, build an SFT dataset, fine-tune a model (LoRA), and generate READMEs from a repo’s file structure.

---

## What Moxi does

- **Collect** READMEs + file trees from awesome-readme-style lists → `data/collection/`
- **Chunk** READMEs for training → `data/chunks/`
- **Generate SFT dataset** (instruction + input + content) via GPT → `data/sft/`
- **Train** a base LLM (e.g. Llama-3.2-3B) with LoRA → model in `models/`
- **Generate docs** for a repo (doc_generator, CLI, web UI)

---

## Quick start

### Prerequisites

- Python 3.11+
- **OpenAI API key** (for SFT dataset generation)
- **Hugging Face token** (for base model; set in `.env` for training)
- **GitHub token** (optional; for crawling)

### Install

```bash
git clone https://github.com/LC0229/moxi.git
cd moxi
python -m venv .venv && source .venv/bin/activate   # or: poetry shell
make install
cp .env.example .env   # edit with API keys
```

### Pipeline (collect → chunk → SFT → train)

```bash
# 1. Collect READMEs (optional: start MongoDB first: docker compose up -d mongodb)
make moxi-collect

# 2. Chunk READMEs
make moxi-chunk

# 3. Build SFT dataset (needs OPENAI_API_KEY in .env)
make generate-sft-dataset

# 4. Train (local GPU)
make moxi-train
```

### Train on AWS (SageMaker)

Set in `.env`: `AWS_S3_BUCKET`, `AWS_ARN_ROLE`, `HUGGINGFACE_ACCESS_TOKEN`. Then:

```bash
poetry install --with aws
make train-aws
```

See **docs/AWS_TRAINING_FLOW_NOW.md** for the full flow.

---

## Project layout

```
moxi/
├── src/
│   ├── moxi_collect/    # Step 1: collect READMEs
│   ├── moxi_chunk/      # Step 2: chunk + repo analysis
│   ├── moxi_train/      # SFT training + SFT dataset generation
│   ├── moxi_data/       # Crawl URLs, review UI, validate data
│   ├── moxi_analyzer/   # Repo analysis (re-export)
│   ├── doc_generator/   # Generate docs for a repo
│   ├── core/            # Config, logging, DB
│   └── cli/             # Command-line interface
├── data/                # Pipeline data (collection, chunks, sft)
├── models/              # Trained checkpoints
├── docs/                # Detailed docs (training, AWS, Docker, MongoDB)
├── TRAINING_WORKFLOW.md # End-to-end training workflow
└── Makefile
```

---

## Commands

| Command | Description |
|--------|-------------|
| `make moxi-collect` | Collect READMEs → `data/collection/` |
| `make moxi-chunk` | Chunk READMEs → `data/chunks/` |
| `make generate-sft-dataset` | Chunks → SFT JSON (needs OpenAI) |
| `make moxi-train` | Train SFT model (local) |
| `make train-aws` | Upload data + submit SageMaker job |
| `make pipeline-dashboard` | Dev dashboard (phases, counts) |
| `make local-generate-docs REPO=url` | Generate docs for a repo |

Run **`make help`** for all targets.

---

## Docs

- **TRAINING_WORKFLOW.md** — Full pipeline, phases, and how to run each step
- **docs/AWS_TRAINING_FLOW_NOW.md** — SageMaker training flow
- **docs/HOW_TRAINING_WORKS.md** — How training and SFT dataset work
- **docs/DOCKER.md** — MongoDB and other services
- **data/README.md** — Data folder layout

---

## License

MIT. See [LICENSE](LICENSE).

---

## Contact

**Shengrui Chen** — [@LC0229](https://github.com/LC0229) · chenleon572@gmail.com
