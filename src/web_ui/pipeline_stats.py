"""Pipeline stats for the dashboard: read collection counts from MongoDB or JSON."""

from pathlib import Path
from typing import Any

from core import get_logger, settings

logger = get_logger(__name__)

DATA_DIR = Path(settings.DATA_DIR)  # data/ (collection, chunks, sft)
COLLECTION_DIR = DATA_DIR / "collection"
README_JSON_PATHS = [
    COLLECTION_DIR / "awesome_readme_clean.json",
    COLLECTION_DIR / "awesome_readme_data.json",
]


def get_collection_count() -> tuple[int, str]:
    """
    Return (count, source) for Phase 1 README samples.
    Tries MongoDB first, then JSON files.
    """
    # Prefer MongoDB (same as llm-twin-course data store)
    try:
        from core.db.mongo import count_readme_samples
        n = count_readme_samples()
        return n, "MongoDB (readme_samples)"
    except Exception as e:
        logger.debug("MongoDB count skipped", error=str(e))

    for p in README_JSON_PATHS:
        if not p.exists():
            continue
        try:
            import json
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return len(data), f"JSON ({p.name})"
            if isinstance(data, dict) and "samples" in data:
                return len(data["samples"]), f"JSON ({p.name})"
        except Exception as e:
            logger.debug("JSON count failed", path=str(p), error=str(e))

    return 0, "—"


def get_sft_count() -> tuple[int, str]:
    """Return (count, source) for Phase 3 SFT samples if available."""
    try:
        from core.db.mongo import get_db
        from core.db.mongo import COLL_SFT_SAMPLES
        n = get_db()[COLL_SFT_SAMPLES].count_documents({})
        return n, "MongoDB (sft_samples)"
    except Exception:
        pass
    sft_path = DATA_DIR / "sft" / "sft_dataset.json"
    if sft_path.exists():
        try:
            import json
            with open(sft_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return len(data), f"JSON ({sft_path.name})"
        except Exception:
            pass
    return 0, "—"


def get_pipeline_stats() -> dict[str, Any]:
    """
    Gather counts and status for each phase (aligned with llm-twin-course workflow).
    Returns dict with phase info and overall status text for the dashboard.
    """
    collect_n, collect_src = get_collection_count()
    sft_n, sft_src = get_sft_count()

    phases = [
        {
            "id": 1,
            "name": "Collect",
            "description": "Fetch READMEs + file trees from awesome-readme lists",
            "output": "awesome_readme_clean.json / readme_samples",
            "count": collect_n,
            "source": collect_src,
            "done": collect_n > 0,
            "status": f"Done — {collect_n} samples" if collect_n > 0 else "Not run",
        },
        {
            "id": 2,
            "name": "Chunk",
            "description": "Split READMEs into chunks (1000–2000 chars)",
            "output": "Chunks + file_tree per repo",
            "count": None,
            "source": "—",
            "done": False,
            "status": "To implement",
        },
        {
            "id": 3,
            "name": "Instructions",
            "description": "GPT-4: one instruction per (chunk, file_tree) → SFT dataset",
            "output": "sft_dataset.json / sft_samples",
            "count": sft_n,
            "source": sft_src,
            "done": sft_n > 0,
            "status": f"Done — {sft_n} samples" if sft_n > 0 else "To implement",
        },
        {
            "id": 4,
            "name": "Train",
            "description": "LoRA/QLoRA fine-tune on SFT dataset",
            "output": "LoRA adapter / model",
            "count": None,
            "source": "—",
            "done": False,
            "status": "To implement",
        },
        {
            "id": 5,
            "name": "Infer",
            "description": "Generate README from file_tree (+ optional description)",
            "output": "README markdown",
            "count": None,
            "source": "—",
            "done": False,
            "status": "To implement",
        },
    ]

    return {
        "phases": phases,
        "collection_count": collect_n,
        "collection_source": collect_src,
        "sft_count": sft_n,
    }
