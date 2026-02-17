"""MongoDB connector for collected and training data (like llm-twin-course).

Use this when you don't want to keep all data in local JSON: store README samples
and SFT samples in MongoDB, then export or stream for training.
"""

from typing import Any, Iterator, Optional

from core import get_logger, settings

logger = get_logger(__name__)

# Collection names
COLL_README_SAMPLES = "readme_samples"
COLL_SFT_SAMPLES = "sft_samples"


def _get_client():
    """Lazy import to avoid requiring pymongo when DB is not used."""
    from pymongo import MongoClient
    return MongoClient(settings.MONGODB_URI)


def get_db():
    """Return the configured MongoDB database."""
    client = _get_client()
    return client[settings.MONGODB_DB_NAME]


def ping() -> bool:
    """Check if MongoDB is reachable."""
    try:
        get_db().command("ping")
        return True
    except Exception as e:
        logger.warning("MongoDB ping failed", error=str(e))
        return False


# ---------- README samples (Phase 1 output: raw collected READMEs + file_tree) ----------


def insert_readme_samples(docs: list[dict[str, Any]]) -> int:
    """Insert many collected README samples (from awesome-readme or crawlers)."""
    if not docs:
        return 0
    db = get_db()
    result = db[COLL_README_SAMPLES].insert_many(docs)
    logger.info("Inserted readme samples", count=len(result.inserted_ids), collection=COLL_README_SAMPLES)
    return len(result.inserted_ids)


def find_readme_samples(
    skip: int = 0,
    limit: int = 100,
    filter_query: Optional[dict] = None,
) -> list[dict]:
    """Return README samples for chunking / instruction generation."""
    db = get_db()
    cur = db[COLL_README_SAMPLES].find(filter_query or {}).skip(skip).limit(limit)
    return list(cur)


def count_readme_samples(filter_query: Optional[dict] = None) -> int:
    """Count README samples (optionally with filter)."""
    return get_db()[COLL_README_SAMPLES].count_documents(filter_query or {})


def stream_readme_samples(
    batch_size: int = 50,
    filter_query: Optional[dict] = None,
) -> Iterator[list[dict]]:
    """Stream README samples in batches (for large datasets without loading all)."""
    db = get_db()
    skip = 0
    while True:
        batch = find_readme_samples(skip=skip, limit=batch_size, filter_query=filter_query)
        if not batch:
            break
        yield batch
        skip += batch_size


# ---------- SFT samples (Phase 3 output: instruction + input + content for training) ----------


def insert_sft_samples(docs: list[dict[str, Any]]) -> int:
    """Insert many SFT samples (instruction, input?, content)."""
    if not docs:
        return 0
    db = get_db()
    result = db[COLL_SFT_SAMPLES].insert_many(docs)
    logger.info("Inserted SFT samples", count=len(result.inserted_ids), collection=COLL_SFT_SAMPLES)
    return len(result.inserted_ids)


def find_sft_samples(
    skip: int = 0,
    limit: Optional[int] = None,
    filter_query: Optional[dict] = None,
) -> list[dict]:
    """Return SFT samples (for export or training)."""
    db = get_db()
    cur = db[COLL_SFT_SAMPLES].find(filter_query or {}).skip(skip)
    if limit is not None:
        cur = cur.limit(limit)
    return list(cur)


def count_sft_samples(filter_query: Optional[dict] = None) -> int:
    """Count SFT samples."""
    return get_db()[COLL_SFT_SAMPLES].count_documents(filter_query or {})


def export_sft_to_list(filter_query: Optional[dict] = None) -> list[dict]:
    """Export all SFT samples to a list (e.g. for JSON dump or HuggingFace Dataset).
    Use with care on very large collections; prefer stream_sft_samples for huge data.
    """
    return find_sft_samples(limit=None, filter_query=filter_query)


def stream_sft_samples(
    batch_size: int = 500,
    filter_query: Optional[dict] = None,
) -> Iterator[list[dict]]:
    """Stream SFT samples in batches (for training data loader or export)."""
    skip = 0
    while True:
        batch = find_sft_samples(skip=skip, limit=batch_size, filter_query=filter_query)
        if not batch:
            break
        yield batch
        skip += batch_size
