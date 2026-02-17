# Moxi step 2: chunk (this package)

Chunk READMEs from collection and optionally analyze one repo (file tree + key files). **One data folder:** `data/` only.

## Steps (moxi): collect → chunk → train

| Stage | Command | Output |
|-------|---------|--------|
| Before (step 1) | `make moxi-collect` | `data/collection/` + MongoDB |
| **Chunk (this step)** | `make moxi-chunk` | `data/chunks/readme_chunks.json` |
| | `make moxi-analyze-repo REPO=url` | (one-repo analysis) |
| After | Phase 3 script, then `make moxi-train` | `data/sft/`, then model |

## Commands

```bash
make moxi-chunk
# or
cd src && PYTHONPATH=.. python -m moxi_chunk.run_feature --output ../data/chunks/readme_chunks.json

make moxi-analyze-repo REPO=https://github.com/owner/repo
```

Optional args for `run_feature`: `--min-length`, `--max-length`, `--source mongo|json|auto`, `--json-path PATH`.

## What we do not use (batch only)

No queue, CDC, bytewax, superlinked, or Qdrant in this step. Can be added later if needed.
