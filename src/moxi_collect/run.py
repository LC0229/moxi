"""
Moxi collection pipeline: gather READMEs + file trees from awesome-readme-style lists.

Output: data/collection/ (JSON) and/or MongoDB readme_samples.
"""

import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

import requests

from core.config import settings

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = settings.GITHUB_TOKEN or os.environ.get("GITHUB_TOKEN")

DATA_DIR = Path(settings.DATA_DIR)
DEFAULT_OUTPUT = str(DATA_DIR / "collection" / "awesome_readme_data.json")

README_LIST_SOURCES = [
    {"name": "awesome-readme", "url": "https://raw.githubusercontent.com/matiassingers/awesome-readme/master/readme.md"},
    {"name": "awesome-readme-examples", "url": "https://raw.githubusercontent.com/sway3406/awesome-readme-examples/master/readme.md"},
    {"name": "jmatembu-awesome-readme", "url": "https://raw.githubusercontent.com/jmatembu/awesome-readme/master/readme.md"},
]


def _parse_repos_from_markdown(content: str, source_name: str) -> List[Dict[str, str]]:
    link_pattern = re.compile(r"\]\s*\(\s*https://github\.com/([^/]+)/([^)/#?]+)[^)]*\)")
    repos_by_key: Dict[str, Dict[str, str]] = {}
    for line in content.splitlines():
        for m in link_pattern.finditer(line):
            owner, repo = m.group(1), m.group(2).rstrip("/")
            if owner.lower() == "github.com" or not repo:
                continue
            key = f"{owner}/{repo}".lower()
            if key in repos_by_key:
                continue
            rest = line[m.end() :].strip()
            description = rest.lstrip("-").strip() if rest.startswith("-") else ""
            repo_url = f"https://github.com/{owner}/{repo}"
            repos_by_key[key] = {"repo_url": repo_url, "owner": owner, "repo": repo, "name": f"{owner}/{repo}", "description": description, "source": source_name}
    return list(repos_by_key.values())


def collect_repos_from_all_sources(source_names: Optional[List[str]] = None) -> List[Dict[str, str]]:
    seen: Dict[str, Dict[str, str]] = {}
    for cfg in README_LIST_SOURCES:
        name = cfg["name"]
        if source_names is not None and name not in source_names:
            continue
        url = cfg["url"]
        print(f"Fetching list: {name} ...")
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            repos = _parse_repos_from_markdown(response.text, name)
            for r in repos:
                key = f"{r['owner']}/{r['repo']}".lower()
                if key not in seen:
                    seen[key] = r
            print(f"   {name}: {len(repos)} links (total unique: {len(seen)})")
        except Exception as e:
            print(f"   Skip {name}: {e}")
    result = list(seen.values())
    print(f"Total: {len(result)} unique repos")
    return result


def fetch_repo_readme(owner: str, repo: str) -> Optional[str]:
    raw_urls = [
        f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
        f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
        f"https://raw.githubusercontent.com/{owner}/{repo}/main/readme.md",
        f"https://raw.githubusercontent.com/{owner}/{repo}/master/readme.md",
    ]
    for raw_url in raw_urls:
        try:
            response = requests.get(raw_url, timeout=10)
            if response.status_code == 200:
                return response.text
        except Exception:
            continue
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        import base64
        return base64.b64decode(response.json()["content"]).decode("utf-8")
    except Exception as e:
        print(f"  Could not fetch README for {owner}/{repo}: {e}")
        return None


def fetch_repo_info(owner: str, repo: str) -> Optional[Dict]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {"language": data.get("language"), "stars": data.get("stargazers_count", 0), "description": data.get("description", ""), "topics": data.get("topics", []), "created_at": data.get("created_at"), "updated_at": data.get("updated_at")}
    except Exception as e:
        print(f"  Could not fetch repo info for {owner}/{repo}: {e}")
        return None


def detect_project_type(readme: str, repo_info: Optional[Dict]) -> str:
    readme_lower = readme.lower()
    repo_info = repo_info or {}
    if "api" in readme_lower or "rest" in readme_lower or "endpoint" in readme_lower:
        return "api"
    elif "web" in readme_lower or "frontend" in readme_lower or "react" in readme_lower:
        return "web_application"
    elif "cli" in readme_lower or "command" in readme_lower or "tool" in readme_lower:
        return "cli_tool"
    elif "library" in readme_lower or "package" in readme_lower or "sdk" in readme_lower:
        return "library"
    elif "framework" in readme_lower:
        return "framework"
    elif "mobile" in readme_lower or "ios" in readme_lower or "android" in readme_lower:
        return "mobile_app"
    return "other"


def get_repo_file_tree(owner: str, repo: str) -> List[str]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/main?recursive=1"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            response = requests.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/master?recursive=1", headers=headers, timeout=10)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        excluded = [".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", ".mypy_cache"]
        return sorted(
            item["path"] for item in data.get("tree", [])
            if item["type"] == "blob" and not any(ex in item["path"] for ex in excluded)
        )
    except Exception as e:
        print(f"  Could not fetch file tree: {e}")
        return []


def collect_awesome_readme_data(
    output_file: str = DEFAULT_OUTPUT,
    limit: Optional[int] = None,
    min_readme_length: int = 500,
    source_names: Optional[List[str]] = None,
) -> None:
    output_path = Path(output_file)
    if not output_path.is_absolute():
        root = Path(settings.DATA_DIR).parent
        output_path = (root / output_file).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Collecting README data (multi-source merge)...")
    repos = collect_repos_from_all_sources(source_names=source_names)
    if limit:
        repos = repos[:limit]
    total_in_list = len(repos)

    existing_by_key: Dict[str, dict] = {}
    existing_failed: List[Dict[str, str]] = []
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                old = json.load(f)
            for s in old.get("training_data", []):
                key = f"{s.get('owner', '')}/{s.get('repo', '')}".lower()
                if key:
                    existing_by_key[key] = s
            existing_failed = old.get("failed", [])
            failed_keys = {f"{f.get('owner', '')}/{f.get('repo', '')}".lower() for f in existing_failed}
            existing_by_key.update({k: {"_failed": True} for k in failed_keys if k})
        except Exception as e:
            print(f"Could not load existing output ({e}), will collect from scratch.")
    training_data = [s for s in existing_by_key.values() if not s.get("_failed")]
    failed = [f for f in existing_failed if isinstance(f, dict)]
    skipped = sum(1 for r in repos if f"{r['owner']}/{r['repo']}".lower() in existing_by_key)
    if skipped:
        print(f"Skipping {skipped} already-collected repos.")
    repos = [r for r in repos if f"{r['owner']}/{r['repo']}".lower() not in existing_by_key]
    print(f"Will collect READMEs from {len(repos)} repos...")
    for i, repo_info in enumerate(repos, 1):
        owner = repo_info["owner"]
        repo = repo_info["repo"]
        print(f"\n[{i}/{len(repos)}] {owner}/{repo}...")
        readme = fetch_repo_readme(owner, repo)
        if not readme:
            failed.append(repo_info)
            continue
        if len(readme) < min_readme_length:
            failed.append(repo_info)
            continue
        repo_metadata = fetch_repo_info(owner, repo) or {}
        project_type = detect_project_type(readme, repo_metadata)
        file_tree = get_repo_file_tree(owner, repo)
        sample = {
            "repo_url": repo_info["repo_url"], "owner": owner, "repo": repo, "name": repo_info["name"],
            "description": repo_info["description"], "project_type": project_type,
            "language": repo_metadata.get("language"), "stars": repo_metadata.get("stars", 0),
            "readme": readme, "readme_length": len(readme), "file_tree": file_tree, "file_count": len(file_tree),
            "source": repo_info.get("source", "awesome-readme"),
        }
        training_data.append(sample)
        print(f"  OK ({len(readme)} chars, {project_type})")
        time.sleep(0.5)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {"total_repos": total_in_list, "collected": len(training_data), "failed": len(failed), "sources": [s["name"] for s in README_LIST_SOURCES], "collection_date": time.strftime("%Y-%m-%d %H:%M:%S")},
            "training_data": training_data,
            "failed": failed,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nDone. Collected: {len(training_data)}, failed: {len(failed)}, saved to {output_path}")
    try:
        from core.db.mongo import ping, insert_readme_samples
        if ping():
            n = insert_readme_samples(training_data)
            print(f"  MongoDB readme_samples: {n} inserted")
    except Exception as e:
        print(f"  MongoDB not written: {e}")
    if training_data:
        avg_len = sum(s["readme_length"] for s in training_data) // len(training_data)
        print(f"  Avg README length: {avg_len} chars. Types: {dict(Counter(s['project_type'] for s in training_data))}")


def push_json_to_mongo(json_path: str) -> bool:
    path = Path(json_path)
    if not path.is_absolute():
        path = Path(settings.DATA_DIR).parent / json_path
    path = path.resolve()
    if not path.exists():
        print(f"File not found: {path}")
        return False
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    training_data = data.get("training_data", [])
    if not training_data:
        print("No training_data in file.")
        return False
    try:
        from core.db.mongo import ping, insert_readme_samples
        if not ping():
            print("MongoDB ping failed.")
            return False
        n = insert_readme_samples(training_data)
        print(f"MongoDB: inserted {n} readme_samples.")
        return True
    except Exception as e:
        print(f"MongoDB error: {e}")
        return False


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Moxi collection pipeline: collect READMEs from awesome-readme-style lists")
    parser.add_argument("--sources", nargs="*", default=None, metavar="NAME", help="Only use these list names")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSON path (default: data/collection/awesome_readme_data.json)")
    parser.add_argument("--limit", type=int, default=None, help="Max repos to collect")
    parser.add_argument("--min-length", type=int, default=500, help="Min README length (chars)")
    parser.add_argument("--push-to-mongo-only", action="store_true", help="Only load JSON and push to MongoDB")
    args = parser.parse_args(argv)

    if args.push_to_mongo_only:
        return 0 if push_json_to_mongo(args.output) else 1
    collect_awesome_readme_data(output_file=args.output, limit=args.limit, min_readme_length=args.min_length, source_names=args.sources)
    return 0


if __name__ == "__main__":
    sys.exit(main())
