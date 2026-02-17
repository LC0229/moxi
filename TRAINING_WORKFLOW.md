# Our training workflow (README generator)

End-to-end flow from raw repos to a model that generates READMEs from a file tree.

---

## Overview

```
[Phase 1] Collect     →  awesome_readme_clean.json
[Phase 2] Chunk       →  (readme_chunks + file_trees per repo)
[Phase 3] Instructions→  sft_dataset.json (instruction + input + content)
[Phase 4] Train       →  LoRA/QLoRA model
[Phase 5] Infer       →  README from (file_tree, optional description)
```

**Pipeline dashboard (dev only):** Run `make pipeline-dashboard` (or `PYTHONPATH=src python -m web_ui.pipeline_dashboard`) to open a **separate** Gradio app for development: full pipeline, current phase, and collection count (e.g. 121 samples). For end users, use `make web-ui` (setup workflows only). Workflow aligned with llm-twin-course (see `PROCESS_COMPARISON.md`).

---

## Limitation: we only use file tree (no real code)

Right now the model is trained and run with **only**:

- **Input:** `file_tree` (list of paths, e.g. `["src/main.py", "requirements.txt"]`) + optional `project_type`.
- **No access to file contents.** The model never sees the actual code.

So it **cannot** read the real code. It can only guess from path names and project type. That means:

- It can learn **structure and style** (sections, tone) from the README `content` in training.
- It **cannot** reliably mention specific APIs, function names, or accurate "how to use" details—those would require seeing the code.

**To generate READMEs that reflect real code**, we need to extend the pipeline to include **code context** in the input (see "Extension: code context" below). Until then, treat outputs as structure- and style-aware drafts, not ground-truth descriptions of the implementation.

---

## Moxi steps and where they live

**One data folder:** `data/` only (see `data/README.md`). No `training_data/`.

**Pipeline packages (all `moxi_*` under `src/`):**

- **moxi_collect** — Step 1: collect READMEs from awesome-readme lists → `data/collection/` + MongoDB
- **moxi_chunk** — Step 2: chunk READMEs + repo analysis (file tree, key files) → `data/chunks/`
- **moxi_train** — Step 3: SFT training → model
- **moxi_data** — Helpers before collect: crawl URLs, review UI, validate/clean data
- **moxi_analyzer** — Repo analysis (re-export from `moxi_chunk.repo_analyzer`); used by moxi_data, doc_generator, web_ui

**Three steps:** **collect** → **chunk** → **train**. Commands: **`make moxi-collect`**, **`make moxi-chunk`**, **`make moxi-train`**.

| Step | Under `src/` | Command |
|------|--------------|---------|
| 1. collect | `moxi_collect` | `make moxi-collect` → `data/collection/` + MongoDB |
| 2. chunk | `moxi_chunk` (chunking + repo analysis) | `make moxi-chunk`, `make moxi-analyze-repo REPO=url` → `data/chunks/` |
| 3. train | `moxi_train` | `make moxi-train` (reads `data/sft/`) |
| (helpers) | `moxi_data`, `moxi_analyzer`, `web_ui`, `core/db` | crawl/review/validate (`moxi_data`); repo analysis (`moxi_analyzer`); MongoDB in `core/db` |

Queue, CDC, bytewax, superlinked, Qdrant not used (batch only). Optional later.

**Repo analysis:** Implementation lives in **`moxi_chunk/repo_analyzer/`**. **`moxi_analyzer`** is a top-level re-export so `moxi_data`, `doc_generator`, and `web_ui` use `from moxi_analyzer import ...`.

---

## How to run each step

**Step 1 (collect):** `data/collection/` + MongoDB.
```bash
docker compose up -d mongodb
make moxi-collect
```
Optional: `scripts/migrate_readme_to_mongo.py` (default: `data/collection/awesome_readme_clean.json`).

**Step 2 (chunk):** `data/chunks/readme_chunks.json`.
```bash
make moxi-chunk
make moxi-analyze-repo REPO=...   # optional
```

**Step 3 and after:** Phase 3 (instructions) → `data/sft/`; then train and infer.

| Step | What | Command |
|------|------|---------|
| Phase 3 | Chunks → SFT samples → `data/sft/` | `make generate-sft-dataset` (needs OPENAI_API_KEY) |
| **3. train** | LoRA/QLoRA on SFT data | `make moxi-train` (local) or `make train-aws` (AWS; see docs/TRAINING_ON_AWS.md) |
| Phase 5 | Infer README from file_tree | (to implement) |

---

## Phase 1: Data collection ✅ (done)

**What:** Fetch READMEs and file trees from awesome-readme list.

**Run:**
```bash
docker compose up -d mongodb   # if using MongoDB
make run-collection
# or: python collect_awesome_readme_data.py   (writes to data/collection/ by default)
# or: cd src && python -m moxi_collect
```
When MongoDB is running and `MONGODB_URI` is set, samples are also written to the `readme_samples` collection. To migrate existing JSON: `python scripts/migrate_readme_to_mongo.py` (default file: `data/collection/awesome_readme_clean.json`).

**Output:** `data/collection/awesome_readme_data.json` (and MongoDB `readme_samples` when configured)

**Shape per item:**
- `repo_url`, `owner`, `repo`, `readme` (full Markdown), `file_tree` (list of paths), `language`, etc.

**Next:** Use `readme` + `file_tree` for chunking and instruction generation.

---

## Phase 2: Chunking (to implement)

**What:** Split each README into chunks (e.g. 1000–2000 chars by sentences) so one README produces many training samples.

**Input:** MongoDB `readme_samples` or `data/collection/awesome_readme_clean.json` (see `docs/FEATURE_PIPELINE.md`).

**Logic (same as llm-twin-course):**
- For each item: `chunk_documents([item["readme"]], min_length=1000, max_length=2000)`
- Keep `file_tree` (and repo metadata) attached to **each chunk** from that repo

**Output (in memory or intermediate file):** list of:
- `chunk`: string (README segment)
- `file_tree`: list[str] (same for all chunks of that repo)
- `repo_url` / `project_type` (optional)

**Why:** 1 README → many chunks → many (instruction, input, content) samples after Phase 3.

---

## Phase 3: Instruction generation ✅ (implemented)

**What:** Use GPT to generate one instruction per (chunk + file_tree). Build the SFT dataset (same as LLM course). **Run:** `make generate-sft-dataset` (set `OPENAI_API_KEY`). **Output:** `data/sft/training_dataset.json`.

**Input:** Chunked list from Phase 2.

**Logic (mirror llm-twin-course `generate.py`):**
1. Batch chunks (e.g. batch_size=3).
2. For each batch, send to GPT-4 a prompt like:
   - “I will give you batches of README sections and their repo file trees. Generate exactly 1 instruction per item. The instruction should describe what kind of README to generate (e.g. for a Python CLI with these files). READMEs should include standard sections: About, Built With, Getting Started, Usage, License (and optionally Roadmap, Contributing, Contact). Output a JSON list of objects with field `instruction` only.”
3. Parse GPT-4 response; pair each `instruction` with the corresponding chunk and file_tree.
4. Build sample: `{ "instruction": "...", "input": { "file_tree": [...], "project_type": "..." }, "content": "<chunk text>" }`.
5. Train/test split (e.g. 90/10); save.

**Output:** `data/sft/sft_dataset.json` (or split into `train.json` / `test.json`)

**Sample shape:**
```json
{
  "instruction": "Generate a README section for a Python web app with FastAPI and the given file structure.",
  "input": {
    "file_tree": ["app/main.py", "app/models.py", "requirements.txt", ...],
    "project_type": "web_application"
  },
  "content": "# My API\n\nA FastAPI service that..."
}
```

---

## Phase 4: Training ✅ (implemented)

**What:** Fine-tune a base LLM (e.g. Llama-3.2-3B) with LoRA/QLoRA on the SFT dataset.

**Input:** `data/sft/sft_dataset.json` (or train split).

**Logic (mirror llm-twin-course `finetune.py`):**
1. Load base model + tokenizer (e.g. Unsloth + 4-bit).
2. Load dataset; map each sample to one training string:
   - **Prompt:** Alpaca-style template with `instruction` + optional `input` (e.g. “File tree: …” or “Project type: …”).
   - **Completion:** `content` (the README chunk).
3. **Optional: merge with public dataset** (implemented like llm-twin-course):
   - Default: `load_dataset("mlabonne/FineTome-Alpaca-100k", split="train[:10000]")` then `concatenate_datasets([custom_dataset, static_dataset])`
   - **CLI:** `--no-public-dataset` to disable; `--public-dataset NAME` and `--public-dataset-size N` to override (or set `MERGE_PUBLIC_DATASET`, `PUBLIC_DATASET_NAME`, `PUBLIC_DATASET_SIZE` in `.env`).
   - **Pros:** General instruction-following; **Cons:** can dilute README-specific signal. Start with merge; use `--no-public-dataset` for README-only.
4. SFTTrainer (or equivalent): LoRA/QLoRA, 2–3 epochs, your choice of batch size and LR.
5. Save adapter or merged model to `models/` (or Hugging Face).

**Output:** Saved model (e.g. `models/readme_model/` or Comet/HF artifact).

---

## Phase 5: Inference (to implement)

**What:** Generate a README given a file tree (and optional short description).

**Input:** List of file paths (e.g. from `git/trees` or local repo) + optional project type or description.

**Logic:**
1. Load the fine-tuned model and tokenizer.
2. Build prompt: same Alpaca template; instruction = e.g. “Generate a README for a project with this file structure”; input = file tree (and optional project type).
3. Generate (e.g. 512–1024 new tokens); decode.
4. Return Markdown string (optionally post-process or split into sections).

Use `readme_structure.get_readme_structure_prompt_suffix()` in the instruction so the model is reminded to include About, Getting Started, Usage, etc. (see `src/readme_structure.py`).

**Output:** README text (e.g. for writing to `README.md` or showing in UI).

---

## Extension: code context (so the model can “see” real code)

Because **file tree alone** is not enough to describe what the code does, we can extend the **input** to include code context:

1. **During collection (Phase 1):** For each repo, fetch not only `file_tree` but also **contents (or summaries)** of key files, e.g.:
   - Entry points: `main.py`, `index.js`, `src/main.ts`, `app.py`, etc.
   - Config: `package.json`, `requirements.txt`, `Cargo.toml`, `README.md` (existing).
   - Optionally: first N lines of each, or an LLM summary per file.
2. **Store in MongoDB / JSON:** e.g. `file_tree` + `key_files`: `{ "path": "src/main.py", "content": "..." }` or `"summary": "..."`.
3. **Phase 2 / 3:** When building chunks and SFT samples, include this in `input`, e.g. `input: { "file_tree": [...], "project_type": "...", "key_files": [...] }`.
4. **SFT trainer:** In `_input_to_text()`, render `key_files` (path + snippet or summary) so the model sees both structure and code.
5. **Inference:** When generating a README for a new repo, fetch the same key files (or summaries) and pass them in the prompt.

Then the model can use real code to generate more accurate READMEs (APIs, usage, dependencies). Implementation can live in `collect_awesome_readme_data.py` (fetch key file contents), a small “key file summarizer” module, and `sft_trainer._input_to_text()` + inference prompt builder.

---

## Order of implementation

| Step | Task                         | Depends on      |
|------|------------------------------|-----------------|
| 1    | Phase 2: Chunking script     | Phase 1 output  |
| 2    | Phase 3: Instruction script  | Phase 2 output  |
| 3    | Phase 4: Training script     | Phase 3 output  |
| 4    | Phase 5: Inference script    | Phase 4 model   |

---

## Data storage (don’t store everything locally)

Like **llm-twin-course**, you can use a DB instead of keeping all data in local JSON.

| Option | Use case | Notes |
|--------|----------|--------|
| **Local JSON** | Small runs, few hundred repos | Current: `awesome_readme_clean.json`, `sft_dataset.json`. Simple; gets heavy with many repos. |
| **MongoDB** | Large collection, many repos, incremental updates | Same idea as llm-twin: store collected READMEs and SFT samples in MongoDB. No single huge file. |
| **Hugging Face Datasets** | Final training set, sharing, no local disk | Push `sft_dataset` to HF; training loads with `load_dataset("org/readme-sft")`. Good for big data and reproducibility. |

### MongoDB (recommended for “too much data locally”)

- **Run:** `docker compose up -d mongodb` or use MongoDB Atlas; set `MONGODB_URI` and `MONGODB_DB_NAME` in `.env`.
- **What we store:** Full documents with real content (not just links). Each doc has `readme` (full Markdown), `file_tree` (list of paths), `repo_url`, `owner`, `repo`, `language`, `stars`, `project_type`. We fetch these fields directly from MongoDB; no separate file storage.
- **Collections:**
  - `readme_samples` — Phase 1 output (repo_url, readme, file_tree, language, …).
  - `sft_samples` — Phase 3 output (instruction, input, content).
- **Usage (from Python):**
  - Store: `from core.db.mongo import insert_readme_samples, insert_sft_samples`
  - Read: `find_readme_samples(skip, limit)`, `export_sft_to_list()` or `stream_sft_samples(batch_size)`.
- **Training from MongoDB:** Export to a JSON file then run training as usual, or add a `--dataset-mongo` path that loads via `export_sft_to_list()` and builds a HuggingFace `Dataset`.

### Hugging Face

- Push your final SFT dataset: `datasets.push_to_hub("your-org/readme-sft", private=True)` (or public).
- Training: `load_dataset("your-org/readme-sft", split="train")` — no need to keep a large local JSON; HF streams/caches.

**Summary:** Use **MongoDB** for the collection pipeline (READMEs + SFT samples) when local JSON is too big; use **Hugging Face** for the final training dataset so you don’t rely on a huge local file.

---

## Files to add (suggested)

- `src/readme_dataset/chunk_documents.py` — reuse or adapt llm-twin-course `chunk_documents`.
- `src/readme_dataset/generate_instructions.py` — load JSON → chunk → batch → GPT-4 → save `sft_dataset.json`.
- `src/moxi_train/readme_finetune.py` — load SFT dataset, Alpaca format, SFTTrainer (or mirror existing `finetune/`).
- `src/inference/readme_generator.py` — load model, format prompt with file_tree, generate README.

You can also keep everything in scripts under `scripts/` until the pipeline is stable, then move into `src/`.
