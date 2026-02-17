"""
Phase 3: Chunks → SFT dataset (instruction, input, content).

Mirrors LLM course: batch chunks, call GPT to generate one instruction per item,
then build Alpaca-style samples for moxi_train.finetune.
"""

import json
import re
import time
from pathlib import Path
from typing import Any

from core import get_logger, settings

logger = get_logger(__name__)

# Optional: use readme_structure hint in prompt
try:
    from readme_structure import get_readme_structure_for_instruction
    README_STRUCTURE_HINT = get_readme_structure_for_instruction()
except Exception:
    README_STRUCTURE_HINT = "Include standard sections: About, Built With, Getting Started, Usage, License."


def load_chunks(path: Path) -> list[dict]:
    """Load chunked features from JSON (format from moxi_chunk)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "features" in data:
        return data["features"]
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return []


def _truncate(s: str, max_len: int = 600) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 3].rstrip() + "..."


def _call_openai_for_instructions(batch: list[dict], batch_size: int = 3) -> list[str]:
    """Call OpenAI to get one instruction per chunk in the batch. Returns list of instruction strings."""
    if not getattr(settings, "OPENAI_API_KEY", None):
        raise RuntimeError("Set OPENAI_API_KEY in .env for instruction generation.")
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("Install openai: pip install openai")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    model = getattr(settings, "OPENAI_MODEL_ID", "gpt-4o-mini")

    # Build prompt: one item per line (preview of chunk + file tree)
    items_text = []
    for i, item in enumerate(batch[:batch_size]):
        chunk_preview = _truncate((item.get("chunk") or ""), 500)
        tree = item.get("file_tree") or []
        tree_preview = ", ".join(tree[:30]) if isinstance(tree, list) else str(tree)
        if len(tree) > 30:
            tree_preview += ", ..."
        items_text.append(f"[Item {i+1}]\nChunk preview:\n{chunk_preview}\n\nFile tree (first 30): {tree_preview}")

    prompt = f"""You are helping build a training dataset for a model that generates README content from a project's file structure.

Below are {len(items_text)} README sections (chunks) with their repo file trees. For each item, output exactly ONE short instruction that describes what kind of README to generate for that project. {README_STRUCTURE_HINT}

Output ONLY a JSON array of strings: one instruction per item, in order. No other text.
Example format: ["Generate a README for a C# OIDC server library with these files.", "Generate a README for a Python CLI tool.", ...]

Items:

"""
    prompt += "\n---\n\n".join(items_text)

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    text = (resp.choices[0].message.content or "").strip()
    # Parse JSON array
    m = re.search(r"\[[\s\S]*\]", text)
    if not m:
        logger.warning("No JSON array in response, using fallback instructions", raw=text[:200])
        return ["Generate a README for this project given the file structure."] * len(batch[:batch_size])
    try:
        instructions = json.loads(m.group(0))
    except json.JSONDecodeError:
        logger.warning("JSON parse failed, using fallback", raw=text[:200])
        return ["Generate a README for this project given the file structure."] * len(batch[:batch_size])
    if not isinstance(instructions, list):
        instructions = [str(instructions)]
    # Pad or trim to match batch size
    n = len(batch[:batch_size])
    while len(instructions) < n:
        instructions.append("Generate a README for this project given the file structure.")
    return instructions[:n]


def build_sft_samples(
    chunks_path: str | Path,
    output_path: str | Path,
    batch_size: int = 3,
    limit: int | None = None,
    train_split: float = 0.9,
) -> tuple[int, str]:
    """
    Load chunks, generate instructions via OpenAI, write SFT dataset.
    Returns (num_samples, output_path).
    """
    path = Path(chunks_path)
    if not path.exists():
        raise FileNotFoundError(f"Chunks file not found: {path}")

    features = load_chunks(path)
    if limit is not None:
        features = features[:limit]
    if not features:
        raise ValueError("No features in chunks file.")

    out = Path(output_path)
    if not out.is_absolute():
        sft_dir = Path(settings.DATA_DIR) / "sft"
        out = sft_dir / (out.name if out.name.endswith(".json") else f"{out}.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    sft_samples: list[dict[str, Any]] = []
    total = len(features)
    for start in range(0, total, batch_size):
        batch = features[start : start + batch_size]
        try:
            instructions = _call_openai_for_instructions(batch, batch_size=batch_size)
        except Exception as e:
            logger.warning("OpenAI call failed, using fallback", error=str(e), start=start)
            instructions = ["Generate a README for this project given the file structure."] * len(batch)
        for item, instr in zip(batch, instructions, strict=False):
            chunk = item.get("chunk") or ""
            file_tree = item.get("file_tree") or []
            project_type = item.get("project_type") or "unknown"
            sft_samples.append({
                "instruction": instr if isinstance(instr, str) else str(instr),
                "input": {"file_tree": file_tree, "project_type": project_type},
                "content": chunk,
            })
        if (start + batch_size) % 30 == 0 or start + batch_size >= total:
            logger.info("Progress", done=min(start + batch_size, total), total=total)
        time.sleep(0.3)  # rate limit

    # Train/val split (optional: trainer does its own split; we can write one file)
    if train_split < 1.0 and len(sft_samples) >= 10:
        import random
        random.seed(42)
        random.shuffle(sft_samples)
        n_train = int(len(sft_samples) * train_split)
        train_data = sft_samples[:n_train]
        val_data = sft_samples[n_train:]
        with open(out, "w", encoding="utf-8") as f:
            json.dump(train_data, f, indent=2, ensure_ascii=False)
        val_path = out.parent / "val_dataset.json"
        with open(val_path, "w", encoding="utf-8") as f:
            json.dump(val_data, f, indent=2, ensure_ascii=False)
        logger.info("Wrote SFT dataset", train=len(train_data), val=len(val_data), path=str(out))
    else:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(sft_samples, f, indent=2, ensure_ascii=False)
        logger.info("Wrote SFT dataset", count=len(sft_samples), path=str(out))

    return len(sft_samples), str(out)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Phase 3: Chunks → SFT dataset (instruction, input, content)")
    parser.add_argument("--chunks", default=None, help="Path to readme_chunks.json (default: data/chunks/ or training_data/)")
    parser.add_argument("--output", "-o", default="training_dataset.json", help="Output filename under data/sft/")
    parser.add_argument("--batch-size", type=int, default=3, help="Chunks per OpenAI call")
    parser.add_argument("--limit", type=int, default=None, help="Max chunks to process (for testing)")
    parser.add_argument("--train-split", type=float, default=0.9, help="Fraction for train (rest = val)")
    args = parser.parse_args()

    data_dir = Path(settings.DATA_DIR)
    root = data_dir.parent
    if args.chunks:
        chunks_path = Path(args.chunks)
    else:
        for candidate in [
            data_dir / "chunks" / "readme_chunks.json",
            root / "training_data" / "readme_chunks.json",
            root / "data" / "chunks" / "readme_chunks.json",
        ]:
            if candidate.exists():
                chunks_path = candidate
                break
        else:
            print("No chunks file found. Run make moxi-chunk first or pass --chunks PATH.", flush=True)
            return 1

    try:
        n, path = build_sft_samples(
            chunks_path,
            args.output,
            batch_size=args.batch_size,
            limit=args.limit,
            train_split=args.train_split,
        )
        print(f"Wrote {n} SFT samples to {path}", flush=True)
        return 0
    except Exception as e:
        logger.exception("Generate SFT dataset failed")
        print(f"Error: {e}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
