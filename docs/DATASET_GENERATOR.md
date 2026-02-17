# Moxi data — README data helpers

**Package:** `src/moxi_data/`. Helpers for **before** the moxi pipeline: get repo URLs, review repos, clean/validate data. Not a separate “generator” pipeline — it feeds into **moxi-collect** (see TRAINING_WORKFLOW.md).

- **Crawl / find / review** → then run `make moxi-collect` to collect READMEs (or use existing JSON/Mongo).
- **Clean / validate** → optional steps on `data/collection/` before chunking.

---

## Linear workflow (README only)

```
1. Get repo URLs     →  crawl GitHub / Awesome lists
2. (Optional) Review →  approve/discard repos in UI
3. Collect READMEs   →  python collect_awesome_readme_data.py  (outside this package)
4. Clean / validate  →  clean_dataset_json, dataset_validator
5. Chunk + train     →  see TRAINING_WORKFLOW.md (Phase 2–5)
```

---

## Step 1 — Get repo URLs

| File | Role |
|------|------|
| **crawlers/github_repo_crawler.py** | Fetches repos from GitHub API (language, stars, type). |
| **crawlers/awesome_list_crawler.py** | Fetches repo links from awesome-* markdown. |
| **repo_fetcher.py** | `fetch_repositories(source, min_stars, limit, ...)` — calls both crawlers, returns one list. |

**Run:** `make crawl-github-repos` or use `fetch_repositories()` in code.

---

## Step 2 — (Optional) Review repos

| File | Role |
|------|------|
| **find_structured_repos.py** | Finds repos with good structure (e.g. docker-compose, multi-module). |
| **review_backend.py** | Backend: load candidates, pre-filter, save approve/discard to `reviewed_repos.json`. |
| **review_ui.py** | Gradio UI for manual approve/discard. |

**Run:** `make review-repos`.

---

## Step 3 — Collect READMEs (outside this package)

Run from repo root:

```bash
python collect_awesome_readme_data.py --output training_data/awesome_readme_clean.json
```

With MongoDB running, samples are also written to the `readme_samples` collection. See **training_data/README.md** and **TRAINING_WORKFLOW.md**.

---

## Step 4 — Clean / validate README data

| File | Role |
|------|------|
| **quality_control/clean_dataset_json.py** | Backup, filter by min readme/content length, write cleaned JSON + report. |
| **quality_control/dataset_validator.py** | Validates sample fields (e.g. instruction/output length). |

**Run:**  
- `make clean-training-data` (cleans `awesome_readme_clean.json`, uses `--min-length 200`).  
- `make validate-dataset` (runs dataset validator).

---

## Makefile targets (README workflow)

| Target | What it does |
|--------|----------------|
| `make crawl-github-repos` | Fetch repo URLs from GitHub. |
| `make find-well-structured-repos` | List well-structured repos to a file. |
| `make review-repos` | Open repo review UI. |
| `make validate-dataset` | Run dataset validator. |
| `make clean-training-data` | Clean README JSON (backup + min length). |

---

## File name → meaning

| File | Meaning |
|------|--------|
| **repo_fetcher** | Fetches list of repo URLs (GitHub + Awesome). |
| **review_backend** | Backend for manual repo review. |
| **review_ui** | Web UI for review. |
| **find_structured_repos** | Finds repos with good structure. |
| **github_repo_crawler** | Crawls GitHub for repos. |
| **awesome_list_crawler** | Crawls awesome-* lists. |
| **dataset_validator** | Validates sample fields. |
| **clean_dataset_json** | Cleans README training JSON. |
