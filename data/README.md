# Data directory (moxi only)

**Single place for all pipeline data.** There is no other data folder (no `training_data/`).

**Pipeline steps (moxi):** **collect** → **chunk** → **train**

| Path | Purpose | Command |
|------|---------|---------|
| `collection/` | Collected READMEs (JSON) | `make moxi-collect` |
| `chunks/` | Chunked READMEs for SFT | `make moxi-chunk` |
| `sft/` | SFT dataset, train/test | Phase 3 script, then `make moxi-train` |
| `repos/` | Cache for cloned repos | optional |

If you still have a root `training_data/` folder, copy its files into these subdirs and remove `training_data/`. See `training_data/README.md` there.
