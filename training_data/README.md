# Deprecated: use `data/` only

**This folder is deprecated.** Moxi uses a single data folder: **`data/`** (see `data/README.md`).

- Copy `awesome_readme_*.json` → `data/collection/`
- Copy `readme_chunks.json` → `data/chunks/`
- Copy any SFT or train files → `data/sft/`

Then you can remove this `training_data/` folder. Pipeline commands: **`make moxi-collect`**, **`make moxi-chunk`**, **`make moxi-train`**.
