# README data sources (for more collection)

The **data collection pipeline** (`collect_awesome_readme_data.py`) pulls from **multiple curated lists** of project READMEs. Repos are merged and deduped by `owner/repo`; each sample keeps a `source` field (e.g. `awesome-readme`, `awesome-readme-examples`).

## Pipeline usage

- **Default:** all configured sources are fetched, parsed, and merged.
- **Restrict sources:**  
  `python collect_awesome_readme_data.py --sources awesome-readme awesome-readme-examples`
- **Add a new list:** append an entry to `README_LIST_SOURCES` in `collect_awesome_readme_data.py` with `name` and raw Markdown `url`. The generic parser extracts any `https://github.com/owner/repo` links from the text.

## Where the instructional stuff is added

The **Best-README-Template** and **Art of README** style guidance is in **`src/readme_structure.py`** (prompts only, not data collection):

- `README_SECTIONS` – list of sections (About, Getting Started, Usage, etc.)
- `get_readme_structure_for_instruction()` – short text for Phase 3 prompts
- `get_readme_structure_prompt_suffix()` – text for Phase 5 inference prompts

TRAINING_WORKFLOW.md references these in Phase 3 and Phase 5.

---

## Configured sources (project READMEs only)

| Source name | Repo | Notes |
|-------------|------|--------|
| `awesome-readme` | [matiassingers/awesome-readme](https://github.com/matiassingers/awesome-readme) | Main list |
| `awesome-readme-examples` | [sway3406/awesome-readme-examples](https://github.com/sway3406/awesome-readme-examples) | Fork with same format |
| `jmatembu-awesome-readme` | [jmatembu/awesome-readme](https://github.com/jmatembu/awesome-readme) | Older fork |

Not used (different flavor):

- [Correia-jpv/fucking-awesome-readme](https://github.com/Correia-jpv/fucking-awesome-readme) – **GitHub profile** READMEs, not project READMEs.
- [sindresorhus/awesome](https://github.com/sindresorhus/awesome) – meta-list of topics; for README-focused data the lists above are used.

## How to add another list

1. Choose a list whose README contains links like `[label](https://github.com/owner/repo)` (project repos only).
2. In `collect_awesome_readme_data.py`, append to `README_LIST_SOURCES`: `{"name": "my-list", "url": "https://raw.githubusercontent.com/org/repo/branch/readme.md"}`.
3. Run collection as usual; the script will fetch, parse, merge, and dedupe.
