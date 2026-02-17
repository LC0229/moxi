# Feature pipeline: what’s in collection, how to run it, what’s after

Chunking and repo analysis live in **`src/moxi_chunk/`**. Data lives under **`data/`** (see `data/README.md`).

1. **Chunking (training path):** `moxi_chunk/chunking.py` + `run_feature.py` — read from `data/collection/` (or MongoDB), chunk READMEs, write `data/chunks/readme_chunks.json`. **Command:** `make moxi-chunk`.
2. **Repo analysis:** `moxi_chunk/repo_analyzer/` — file tree, key files, project type/language. **Command:** `make moxi-analyze-repo REPO=url`.

---

## What’s in the collection right now

**MongoDB collection:** `readme_samples` (DB: `mongo` / from `MONGODB_DB_NAME`).

Each document has:

| Field           | Type     | Description |
|----------------|----------|-------------|
| `repo_url`      | string   | Full GitHub URL |
| `owner`        | string   | GitHub owner |
| `repo`         | string   | Repo name |
| `name`         | string   | Repo display name from list |
| `description`  | string   | Repo description (optional) |
| `project_type` | string   | e.g. `api`, `web_application`, `cli`, `library` |
| `language`     | string   | Primary language (optional) |
| `stars`        | int      | Star count (optional) |
| **`readme`**   | string   | Full README markdown |
| `readme_length`| int      | Character count |
| **`file_tree`**| list[str]| Paths in the repo (e.g. `["src/main.py", "README.md"]`) |
| `file_count`   | int      | `len(file_tree)` |
| `source`       | string   | e.g. `awesome-readme`, `awesome-readme-examples` |

**Current count:** e.g. **121** documents (see pipeline dashboard or `count_readme_samples()`).

Same shape is in **JSON**: `training_data/awesome_readme_clean.json` or `awesome_readme_data.json` (array in `training_data` key or top-level array).

---

## How to do “feature” right now

In the architecture diagram, the **Feature pipeline** is: *Collection (MongoDB) → process → features (e.g. chunks) → optionally Vector DB (Qdrant).*

For **training** we don’t need Qdrant. “Feature” here = **chunked READMEs + file_tree** ready for Phase 3 (instruction generation).

### Option A – Training path (recommended next step)

1. **Read** from MongoDB `readme_samples` (or from JSON).
2. **Chunk** each `readme` (e.g. 1000–2000 chars, sentence boundaries).
3. **Output** one “feature” per chunk: `{ "chunk", "file_tree", "repo_url", "project_type" }` → feed into Phase 3 (instructions) then Train.

**Run:**

```bash
make run-feature
# or from repo root:
cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_chunk.run_feature --output ../data/chunks/readme_chunks.json
```

This reads from MongoDB (or `data/collection/` JSON), chunks each README, and writes `data/chunks/readme_chunks.json`. No queue, CDC, bytewax, superlinked, or Qdrant in this path.

### Option B – RAG path (optional)

If you want a **Vector DB** for retrieval (e.g. “find similar READMEs”):

1. Use the same chunking as above.
2. Embed each chunk (e.g. `BAAI/bge-small-en-v1.5`).
3. Upsert into Qdrant (e.g. collection `readme_chunks`).

That’s a separate script (e.g. `scripts/embed_readme_chunks_to_qdrant.py`) once chunking exists.

---

## What we want after feature

After the **feature** step (chunked READMEs + file_tree):

| Step        | What |
|------------|------|
| **Phase 3** | **Instructions** – GPT-4: one instruction per (chunk, file_tree) → build SFT samples `{ instruction, input, content }` → save to `sft_dataset.json` or `sft_samples` in MongoDB. |
| **Phase 4** | **Train** – LoRA/QLoRA on SFT dataset. |
| **Phase 5** | **Infer** – Generate README from file_tree (and optional description). |

So the order is:

**Collection (done) → Feature (chunking; run script above) → Phase 3 (instructions) → Phase 4 (train) → Phase 5 (infer).**

---

## Summary

- **In collection now:** 121 (or N) docs with `readme`, `file_tree`, `project_type`, etc.
- **Do feature now:** Run `scripts/run_feature_from_collection.py` to chunk and produce `readme_chunks.json` (or equivalent).
- **After feature:** Run Phase 3 (instruction generation), then Train, then Infer.
