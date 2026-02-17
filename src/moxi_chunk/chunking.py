"""Chunk READMEs from collection (Mongo/JSON) → features for Phase 3. Batch only; no queue/CDC/vector DB."""

import json
import re
from pathlib import Path
from typing import Literal

from core import get_logger, settings

logger = get_logger(__name__)

DATA_DIR = Path(settings.DATA_DIR)  # data/ (collection, chunks, sft)
ROOT = DATA_DIR.parent


def chunk_by_sentences(
    text: str,
    min_length: int = 1000,
    max_length: int = 2000,
) -> list[str]:
    """Split text into chunks by sentence boundaries within min/max character length."""
    if not text:
        return []
    if len(text) <= max_length:
        return [text] if len(text) >= min_length else [text]
    parts = re.split(r"(?<=[.!?])\s+|\n\n+", text)
    parts = [p.strip() for p in parts if p.strip()]
    chunks = []
    current = []
    current_len = 0
    for p in parts:
        need = len(p) + (1 if current else 0)
        if current_len + need <= max_length:
            current.append(p)
            current_len += need
        else:
            if current:
                joined = "\n\n".join(current)
                if len(joined) >= min_length:
                    chunks.append(joined)
            if len(p) > max_length:
                for i in range(0, len(p), max_length):
                    chunks.append(p[i : i + max_length])
                current = []
                current_len = 0
            else:
                current = [p]
                current_len = len(p)
    if current:
        joined = "\n\n".join(current)
        if len(joined) >= min_length or not chunks:
            chunks.append(joined)
    return chunks


def load_collection_from_mongo() -> list[dict]:
    """Load readme_samples from MongoDB."""
    from core.db.mongo import find_readme_samples

    out = []
    skip = 0
    limit = 200
    while True:
        batch = find_readme_samples(skip=skip, limit=limit)
        if not batch:
            break
        out.extend(batch)
        skip += limit
        if len(batch) < limit:
            break
    return out


def load_collection_from_json(path: Path) -> list[dict]:
    """Load from awesome_readme_clean.json or awesome_readme_data.json."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "training_data" in data:
        return data["training_data"]
    return []


def run_chunking(
    output_path: str = "data/chunks/readme_chunks.json",
    min_length: int = 1000,
    max_length: int = 2000,
    source: Literal["mongo", "json", "auto"] = "auto",
    json_path: str | None = None,
) -> tuple[int, str]:
    """
    Read collection (Mongo or JSON), chunk READMEs, write features to output_path.
    Returns (num_chunks, absolute_output_path).
    """
    docs: list[dict] = []
    if source in ("mongo", "auto"):
        try:
            from core.db.mongo import ping
            if ping():
                docs = load_collection_from_mongo()
                logger.info("Loaded from MongoDB readme_samples", count=len(docs))
        except Exception as e:
            if source == "mongo":
                raise
            logger.debug("MongoDB skipped", error=str(e))
    if not docs and source in ("json", "auto"):
        base = Path(json_path) if json_path else DATA_DIR / "collection" / "awesome_readme_clean.json"
        if not base.exists():
            base = DATA_DIR / "collection" / "awesome_readme_data.json"
        if base.exists():
            docs = load_collection_from_json(Path(base))
            logger.info("Loaded from JSON", path=str(base), count=len(docs))
    if not docs:
        raise RuntimeError("No collection data. Run collection first (e.g. collect_awesome_readme_data.py).")

    features = []
    for doc in docs:
        readme = doc.get("readme") or ""
        file_tree = doc.get("file_tree") or []
        repo_url = doc.get("repo_url") or ""
        project_type = doc.get("project_type") or "unknown"
        owner = doc.get("owner") or ""
        repo = doc.get("repo") or ""
        for ch in chunk_by_sentences(readme, min_length=min_length, max_length=max_length):
            features.append({
                "chunk": ch,
                "file_tree": file_tree,
                "repo_url": repo_url,
                "project_type": project_type,
                "owner": owner,
                "repo": repo,
            })

    out = Path(output_path)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"features": features, "num_chunks": len(features)}, f, indent=2, ensure_ascii=False)

    return len(features), str(out)
