"""
Find well-structured system-level repositories.

Based on Cursor task description:
- Multi-component/services
- Has docker-compose.yml, k8s/, terraform/, or multi-module structure
- Real applications, not tutorials
- 20+ stars preferred
- Backend languages: Node.js, Go, Python, Java
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import requests

from core import get_logger, settings
from moxi_analyzer import analyze_repository
from moxi_analyzer.parsers.project_validator import is_valid_coding_project

logger = get_logger(__name__)


class WellStructuredRepoFinder:
    """Find well-structured system-level repositories."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.token = github_token or settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
    
    def has_structure_indicators(self, repo_analysis) -> bool:
        """
        Check if repository has structure indicators.
        
        Indicators:
        - docker-compose.yml
        - k8s/ or helm/ directories
        - terraform/ or .tf files
        - Multi-module structure (services/, apps/, packages/, cmd/)
        """
        repo_path = repo_analysis.path
        
        # Check for docker-compose.yml
        if (repo_path / "docker-compose.yml").exists() or (repo_path / "docker-compose.yaml").exists():
            return True
        
        # Check for Kubernetes manifests
        if (repo_path / "k8s").exists() or (repo_path / "helm").exists():
            return True
        
        # Check for Terraform
        if (repo_path / "terraform").exists() or list(repo_path.rglob("*.tf")):
            return True
        
        # Check for multi-module structure
        multi_module_dirs = ["services", "apps", "packages", "cmd", "modules", "microservices"]
        for dir_name in multi_module_dirs:
            if (repo_path / dir_name).exists():
                return True
        
        return False
    
    def is_well_structured(self, repo_url: str, repo_info: Optional[Dict] = None) -> bool:
        """
        Check if repository is well-structured system-level project.
        
        Criteria:
        1. Has structure indicators (docker-compose, k8s, terraform, multi-module)
        2. Is valid coding project (not tutorial/demo/awesome-list)
        3. Has multiple components (multiple files in different directories)
        4. Not a single-file or single-service project
        """
        try:
            # Pre-filter: Check repo info if available (before cloning)
            if repo_info:
                if self._should_exclude_repo(repo_info):
                    logger.debug("Excluded: repo info contains exclude keywords", url=repo_url)
                    return False
            
            # Analyze repository
            repo_analysis = analyze_repository(
                repo_url,
                cache_dir=settings.REPO_CACHE_DIR
            )
            
            # Check if valid coding project (not tutorial/demo)
            # Pass repo_info to validator for better filtering
            repo_info_dict = {
                "description": repo_info.get("description", "") if repo_info else "",
                "topics": repo_info.get("topics", []) if repo_info else [],
            } if repo_info else None
            
            if not is_valid_coding_project(repo_analysis.path, repo_info=repo_info_dict):
                logger.debug("Excluded: not a valid coding project", url=repo_url)
                return False
            
            # Check for structure indicators
            if not self.has_structure_indicators(repo_analysis):
                logger.debug("Excluded: no structure indicators", url=repo_url)
                return False
            
            # Check for multiple components (at least 5 code files in different dirs)
            code_extensions = {".py", ".js", ".java", ".go", ".ts", ".tsx"}
            code_files = [f for f in repo_analysis.path.rglob("*") 
                         if f.is_file() and f.suffix in code_extensions]
            
            if len(code_files) < 5:
                logger.debug("Excluded: insufficient code files", 
                           url=repo_url, count=len(code_files))
                return False
            
            # Check files are in different directories (not all in one place)
            code_dirs = {f.parent for f in code_files}
            if len(code_dirs) < 2:
                logger.debug("Excluded: all files in one directory", url=repo_url)
                return False
            
            # Check for multiple top-level directories (indicates multi-module structure)
            top_level_dirs = [d for d in repo_analysis.path.iterdir() 
                            if d.is_dir() and not d.name.startswith('.') 
                            and d.name not in ['node_modules', '__pycache__', '.git', 'venv', 'env']]
            
            if len(top_level_dirs) < 2:
                logger.debug("Excluded: insufficient top-level directories", url=repo_url)
                return False
            
            # Additional check: Should have at least one main application file
            main_files = ["main.py", "app.py", "server.py", "index.js", "main.go", "Application.java"]
            has_main_file = any((repo_analysis.path / f).exists() for f in main_files) or \
                          any("main" in str(f.name).lower() for f in code_files[:10])
            
            if not has_main_file:
                logger.debug("Excluded: no main application file found", url=repo_url)
                return False
            
            logger.info("✅ Found well-structured repository", url=repo_url)
            return True
            
        except Exception as e:
            logger.debug("Error checking repository", url=repo_url, error=str(e))
            return False
    
    def _should_exclude_repo(self, repo: Dict) -> bool:
        """
        Check if repository should be excluded (awesome-list, tutorial, etc.).
        
        Args:
            repo: Repository dict with url, name, description, etc.
            
        Returns:
            True if should be excluded, False otherwise
        """
        exclude_keywords = [
            "awesome", "awesome-list", "awesome-list",
            "list", "curated", "collection", "resources",
            "tutorial", "tutorials", "course", "courses",
            "learning", "learn", "education", "educational",
            "example", "examples", "demo", "demos",
            "boilerplate", "template", "templates",
            "starter", "starters", "scaffold", "scaffolding",
            "sample", "samples", "playground", "practice"
        ]
        
        # Check name
        name_lower = repo.get("name", "").lower()
        if any(keyword in name_lower for keyword in exclude_keywords):
            logger.debug("Excluded: name contains exclude keywords", name=name_lower)
            return True
        
        # Check description
        description = (repo.get("description") or "").lower()
        if any(keyword in description for keyword in exclude_keywords):
            logger.debug("Excluded: description contains exclude keywords", 
                        description=description[:100])
            return True
        
        # Check if it's an awesome-list repository (common patterns)
        owner = repo.get("owner", "").lower()
        if "awesome" in owner or "awesome" in name_lower:
            logger.debug("Excluded: likely awesome-list", owner=owner, name=name_lower)
            return True
        
        return False
    
    def search_github(
        self,
        query: str,
        min_stars: int = 20,
        limit: int = 100,
        exclude_keywords: bool = True
    ) -> List[Dict]:
        """
        Search GitHub for repositories matching query.
        
        Args:
            query: GitHub search query
            min_stars: Minimum stars
            limit: Maximum results
            exclude_keywords: If True, exclude awesome-list, tutorial, etc. in search query
            
        Returns:
            List of repository info dicts
        """
        repos = []
        per_page = 100
        pages = (limit + per_page - 1) // per_page
        
        # Add exclusion to search query
        if exclude_keywords:
            exclude_query = " -awesome -list -tutorial -example -demo -boilerplate -template -starter"
            query = query + exclude_query
        
        for page in range(1, pages + 1):
            try:
                url = f"{self.base_url}/search/repositories"
                params = {
                    "q": f"{query} stars:>={min_stars}",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": min(per_page, limit - len(repos)),
                    "page": page
                }
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                items = data.get("items", [])
                
                for item in items:
                    repo = {
                        "url": item["html_url"],
                        "owner": item["owner"]["login"],
                        "name": item["name"],
                        "stars": item["stargazers_count"],
                        "description": item.get("description", ""),
                        "language": item.get("language", ""),
                        "topics": item.get("topics", []),
                    }
                    
                    # Filter out awesome-list, tutorial, etc.
                    if self._should_exclude_repo(repo):
                        continue
                    
                    repos.append(repo)
                
                if len(repos) >= limit or len(items) == 0:
                    break
                
                # Rate limit
                time.sleep(2)
                
            except Exception as e:
                logger.error("GitHub API error", error=str(e))
                break
        
        return repos[:limit]
    
    def find_well_structured_repos(
        self,
        languages: List[str] = ["Python", "JavaScript", "Go", "Java"],
        min_stars: int = 20,
        limit: int = 200
    ) -> List[str]:
        """
        Find well-structured system-level repositories.
        
        Args:
            languages: Preferred languages
            min_stars: Minimum stars
            limit: Maximum repos to check
            
        Returns:
            List of repository URLs
        """
        all_repos = []
        
        # Search queries for well-structured repos
        # Use specific queries that target real applications
        queries = [
            # Docker-based applications
            "docker-compose.yml language:Python -awesome -tutorial",
            "docker-compose.yml language:JavaScript -awesome -tutorial",
            "docker-compose.yml language:Go -awesome -tutorial",
            
            # Kubernetes applications
            "language:Python path:k8s -awesome -tutorial",
            "language:JavaScript path:k8s -awesome -tutorial",
            "language:Go path:k8s -awesome -tutorial",
            
            # Microservices architecture
            "microservices language:Python -awesome -tutorial -example",
            "microservices language:JavaScript -awesome -tutorial -example",
            "microservices language:Go -awesome -tutorial -example",
            
            # Multi-service applications
            "path:services language:Python -awesome -tutorial",
            "path:apps language:JavaScript -awesome -tutorial",
            "path:cmd language:Go -awesome -tutorial",
            
            # Infrastructure as code
            "terraform language:Python -awesome -tutorial",
            "serverless.yml language:JavaScript -awesome -tutorial",
        ]
        
        logger.info("Searching for well-structured repositories", 
                   languages=languages,
                   min_stars=min_stars)
        
        for query in queries:
            repos = self.search_github(query, min_stars=min_stars, limit=limit // len(queries))
            all_repos.extend(repos)
            
            # Remove duplicates
            seen = set()
            unique_repos = []
            for repo in all_repos:
                key = repo["url"]
                if key not in seen:
                    seen.add(key)
                    unique_repos.append(repo)
            all_repos = unique_repos
            
            if len(all_repos) >= limit:
                break
        
        logger.info("Found candidate repositories", total=len(all_repos))
        
        # Filter for well-structured repos
        well_structured = []
        for i, repo in enumerate(all_repos[:limit], 1):
            logger.info("Checking repository", 
                       progress=f"{i}/{min(len(all_repos), limit)}",
                       url=repo["url"],
                       name=repo["name"])
            
            # Pass repo info for pre-filtering
            if self.is_well_structured(repo["url"], repo_info=repo):
                well_structured.append(repo["url"])
                logger.info("✅ Well-structured repository found", 
                          url=repo["url"],
                          stars=repo.get("stars", 0),
                          language=repo.get("language", ""))
            
            # Rate limiting
            if i % 10 == 0:
                time.sleep(1)
        
        logger.info("Well-structured repositories found", count=len(well_structured))
        return well_structured


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Find well-structured system-level repositories")
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["Python", "JavaScript", "Go", "Java"],
        help="Preferred languages"
    )
    parser.add_argument(
        "--min-stars",
        type=int,
        default=20,
        help="Minimum stars (default: 20)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum repositories to check (default: 200)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(settings.DATA_DIR) / "collection" / "well_structured_repos.txt"),
        help="Output file (one URL per line)"
    )
    
    args = parser.parse_args()
    
    finder = WellStructuredRepoFinder()
    repos = finder.find_well_structured_repos(
        languages=args.languages,
        min_stars=args.min_stars,
        limit=args.limit
    )
    
    # Save as plain list (one URL per line)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for repo_url in repos:
            f.write(f"{repo_url}\n")
    
    logger.info("✅ Results saved", 
               file=str(output_file),
               repos_count=len(repos))
    
    print(f"\n✅ Found {len(repos)} well-structured repositories")
    print(f"📁 Saved to: {args.output}")
    print("\nRepository URLs:")
    for repo_url in repos[:10]:  # Show first 10
        print(f"  {repo_url}")
    if len(repos) > 10:
        print(f"  ... and {len(repos) - 10} more")


if __name__ == "__main__":
    main()

