"""
Repository Reviewer - Backend for manual repository review.

This module:
1. Fetches candidate repositories
2. Pre-filters obviously bad ones
3. Provides data for frontend review
4. Saves user decisions
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core import get_logger, settings
from moxi_data.repo_fetcher import fetch_repositories
from moxi_data.find_structured_repos import WellStructuredRepoFinder
from moxi_analyzer import analyze_repository
from moxi_analyzer.models import ProjectType
from moxi_analyzer.parsers.project_validator import is_valid_coding_project

logger = get_logger(__name__)


class RepositoryReviewer:
    """Backend for manual repository review."""
    
    def __init__(self, output_file: str = ""):
        self.output_file = Path(output_file) if output_file else Path(settings.DATA_DIR) / "collection" / "reviewed_repos.json"
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.reviewed_repos = self._load_reviewed()
        
    def _load_reviewed(self) -> Dict:
        """Load previously reviewed repositories."""
        if self.output_file.exists():
            with open(self.output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"kept": [], "discarded": []}
    
    def _save_reviewed(self):
        """Save reviewed repositories."""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.reviewed_repos, f, indent=2, ensure_ascii=False)
    
    def pre_filter_repo(self, repo_url: str) -> Tuple[bool, str]:
        """
        Pre-filter repository by analyzing code content (like Cursor).
        
        This method:
        1. Reads and analyzes code files (not just filenames)
        2. Detects components from actual code (Flask, Database, Cache, etc.)
        3. Understands project structure from code patterns
        4. Determines if it has basic project structure (frontend/backend/data layers)
        
        Returns:
            (should_review, reason)
        """
        try:
            # Step 1: Analyze repository structure
            repo_analysis = analyze_repository(
                repo_url,
                cache_dir=settings.REPO_CACHE_DIR
            )
            
            # Step 2: Quick check - is valid coding project
            if not is_valid_coding_project(repo_analysis.path):
                return False, "Not a valid coding project"
            
            # Step 2.5: CRITICAL - Exclude libraries and simple CLI tools
            # We only want complete software with frontend/backend/data architecture
            project_type = repo_analysis.project_type
            if project_type == ProjectType.LIBRARY:
                return False, f"Excluded: Library project (not a complete software/application). Libraries are packages/modules for other projects to use, not standalone applications."
            
            # IMPORTANT: Exclude simple CLI tools (like youtube-dl)
            # Simple CLI tools don't have frontend/backend/data architecture
            # We only want CLI tools that are part of larger systems (e.g., CLI + API + Database)
            if project_type == ProjectType.CLI:
                # Check if it's a simple CLI tool (no architecture) or a CLI with full architecture
                # We'll check architecture layers later, but for now, note that simple CLI will be filtered out
                pass  # Will be filtered out by architecture layer check below
            
            # Only accept APPLICATION (or CLI that has full architecture)
            if project_type not in [ProjectType.APPLICATION, ProjectType.CLI]:
                # Check if it has application-like structure despite being UNKNOWN
                # Look for entry points that indicate it's a runnable application
                key_files = repo_analysis.key_files
                entry_points = ["main.py", "app.py", "server.py", "manage.py", "wsgi.py", "asgi.py", "application.py"]
                has_entry_point = any(ep in [f.name.lower() for f in key_files.values()] for ep in entry_points)
                
                if not has_entry_point:
                    return False, f"Excluded: Project type is '{project_type.value}' and no application entry point found (main.py, app.py, server.py, etc.). Need complete software/application, not library or unknown project."
            
            # Step 3: Analyze code content (like Cursor does)
            # This reads actual code files and detects components
            from repo_analyzer.architecture.analyzer import analyze_architecture_with_rules
            
            rule_analysis = analyze_architecture_with_rules(repo_analysis)
            components = rule_analysis.get('components', [])
            connections = rule_analysis.get('connections', [])
            
            # Step 4: Understand project structure from code content
            # Detect layers from actual components (not just directory names)
            
            # Frontend/API Layer: Detected from code
            has_api_server = any(
                c.get('name') in ['API Server', 'Web Server'] 
                for c in components
            )
            
            # Application Layer: Detected from code
            has_business_logic = any(
                c.get('type') == 'application' or c.get('name') == 'Business Logic'
                for c in components
            )
            
            # Data Layer: Detected from code
            has_database = any(
                c.get('type') == 'database'
                for c in components
            )
            has_cache = any(
                c.get('type') == 'cache'
                for c in components
            )
            has_storage = any(
                c.get('type') == 'storage'
                for c in components
            )
            
            # Check if has basic project structure (at least 2 layers)
            frontend_layer = has_api_server
            application_layer = has_business_logic
            data_layer = has_database or has_cache or has_storage
            
            layers_count = sum([frontend_layer, application_layer, data_layer])
            
            # CRITICAL: Must have at least 2 architectural layers
            # This filters out simple CLI tools (like youtube-dl) that don't have frontend/backend/data structure
            if layers_count < 2:
                detected_components = [c.get('name', 'Unknown') for c in components]
                project_type_str = project_type.value if project_type else "unknown"
                return False, f"Excluded: Simple {project_type_str} tool (like youtube-dl) - only {layers_count} layer(s) detected. Need complete software with frontend/backend/data architecture. Components: {', '.join(detected_components[:5])}"
            
            # Step 5: Check for minimum components (at least 3 different components)
            if len(components) < 3:
                return False, f"Too few components detected: {len(components)} < 3. Need at least API/Server + Application + Data layer"
            
            # Step 6: Check for connections (components should interact)
            if len(connections) == 0 and len(components) < 4:
                # If no connections detected and few components, might be too simple
                return False, "No component connections detected - project might be too simple"
            
            # Step 7: Additional validation - has enough code files (but not too many)
            code_extensions = {".py", ".js", ".java", ".go", ".ts", ".tsx", ".jsx"}
            code_files = [f for f in repo_analysis.path.rglob("*") 
                         if f.is_file() and f.suffix in code_extensions]
            
            if len(code_files) < 10:
                return False, f"Too few code files: {len(code_files)} < 10"
            
            # IMPORTANT: Filter out very large repositories (hard to analyze, often complex)
            # Start with smaller repos (easier to understand for README collection)
            MAX_CODE_FILES = 500  # Reasonable limit for initial dataset
            if len(code_files) > MAX_CODE_FILES:
                return False, f"Repository too large: {len(code_files)} files > {MAX_CODE_FILES}. Start with smaller repos for better quality."
            
            # Step 8: Files should be in multiple directories (indicates structure)
            code_dirs = {f.parent for f in code_files}
            if len(code_dirs) < 3:
                return False, f"Files in too few directories: {len(code_dirs)} < 3"
            
            # Success: Has basic project structure detected from code
            component_names = [c.get('name', 'Unknown') for c in components]
            logger.info("Project structure detected from code",
                       url=repo_url,
                       components=component_names,
                       layers=layers_count,
                       connections=len(connections))
            
            return True, f"OK - {layers_count} layers, {len(components)} components detected from code"
            
        except Exception as e:
            logger.error("Error pre-filtering repository", url=repo_url, error=str(e))
            return False, f"Error: {str(e)}"
    
    def get_repo_info(self, repo_url: str) -> Optional[Dict]:
        """
        Get repository information for display.
        
        Returns:
            Dict with repo info, file tree, structure analysis
        """
        try:
            repo_analysis = analyze_repository(
                repo_url,
                cache_dir=settings.REPO_CACHE_DIR
            )
            
            # Get file tree (limited depth)
            file_tree = self._get_file_tree(repo_analysis.path, max_depth=3)
            
            # Get structure analysis
            structure = self._analyze_structure(repo_analysis.path)
            
            return {
                "url": repo_url,
                "project_type": repo_analysis.project_type.value,
                "project_language": repo_analysis.project_language.value,
                "file_tree": file_tree,
                "structure": structure,
                "key_files": {k: str(v) for k, v in repo_analysis.key_files.items()},
            }
            
        except Exception as e:
            logger.error("Error getting repo info", url=repo_url, error=str(e))
            return None
    
    def _get_file_tree(self, repo_path: Path, max_depth: int = 3) -> str:
        """Get file tree representation."""
        lines = []
        
        def build_tree(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return
            
            try:
                items = sorted([item for item in path.iterdir() 
                               if not item.name.startswith('.') 
                               and item.name not in ['node_modules', '__pycache__', '.git', 'venv', 'env', 'dist', 'build']],
                              key=lambda x: (x.is_file(), x.name.lower()))
                
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    lines.append(f"{prefix}{current_prefix}{item.name}")
                    
                    if item.is_dir():
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        build_tree(item, next_prefix, depth + 1)
            except Exception:
                pass
        
        build_tree(repo_path)
        return "\n".join(lines[:200])  # Limit to 200 lines
    
    def _analyze_structure(self, repo_path: Path) -> Dict:
        """Analyze repository structure."""
        structure = {
            "has_frontend": False,
            "has_backend": False,
            "has_server": False,
            "has_api": False,
            "has_database": False,
            "has_docker": False,
            "has_k8s": False,
            "top_level_dirs": [],
            "code_file_count": 0,
            "code_dirs": 0,
        }
        
        # Check directories
        top_level_dirs = [d.name for d in repo_path.iterdir() 
                         if d.is_dir() and not d.name.startswith('.')
                         and d.name not in ['node_modules', '__pycache__', '.git', 'venv', 'env']]
        structure["top_level_dirs"] = top_level_dirs
        
        # Check for frontend/backend/server
        structure["has_frontend"] = any(d in ["frontend", "client", "web", "ui"] for d in top_level_dirs)
        structure["has_backend"] = any(d in ["backend", "server", "api", "services"] for d in top_level_dirs)
        structure["has_server"] = any(d in ["server", "api"] for d in top_level_dirs)
        structure["has_api"] = "api" in top_level_dirs or any("api" in d.lower() for d in top_level_dirs)
        
        # Check for database
        structure["has_database"] = any(d in ["db", "database", "models", "migrations"] for d in top_level_dirs)
        
        # Check for docker/k8s
        structure["has_docker"] = (repo_path / "docker-compose.yml").exists() or (repo_path / "Dockerfile").exists()
        structure["has_k8s"] = (repo_path / "k8s").exists() or (repo_path / "helm").exists()
        
        # Count code files
        code_extensions = {".py", ".js", ".java", ".go", ".ts", ".tsx", ".jsx"}
        code_files = [f for f in repo_path.rglob("*") 
                     if f.is_file() and f.suffix in code_extensions]
        structure["code_file_count"] = len(code_files)
        structure["code_dirs"] = len({f.parent for f in code_files})
        
        return structure
    
    def mark_repo(self, repo_url: str, decision: str):
        """
        Mark repository as kept or discarded.
        
        Args:
            repo_url: Repository URL
            decision: "keep" or "discard"
        """
        if decision == "keep":
            if repo_url not in self.reviewed_repos["kept"]:
                self.reviewed_repos["kept"].append(repo_url)
                if repo_url in self.reviewed_repos["discarded"]:
                    self.reviewed_repos["discarded"].remove(repo_url)
        elif decision == "discard":
            if repo_url not in self.reviewed_repos["discarded"]:
                self.reviewed_repos["discarded"].append(repo_url)
                if repo_url in self.reviewed_repos["kept"]:
                    self.reviewed_repos["kept"].remove(repo_url)
        
        self._save_reviewed()
        logger.info("Repository marked", url=repo_url, decision=decision)
    
    def remove_from_kept(self, repo_url: str):
        """
        Remove repository from kept list (if user accidentally clicked keep).
        
        Args:
            repo_url: Repository URL to remove
        """
        if repo_url in self.reviewed_repos["kept"]:
            self.reviewed_repos["kept"].remove(repo_url)
            self._save_reviewed()
            logger.info("Repository removed from kept", url=repo_url)
            return True
        return False
    
    def get_kept_repos(self) -> list:
        """
        Get list of kept repositories.
        
        Returns:
            List of repository URLs
        """
        return self.reviewed_repos.get("kept", [])
    
    def get_candidate_repos(
        self,
        source: str = "github",
        min_stars: int = 10,
        limit: int = 100
    ) -> List[str]:
        """
        Get candidate repositories (pre-filtered).
        
        Args:
            source: "github" or "well_structured"
            min_stars: Minimum stars
            limit: Maximum repos to fetch
            
        Returns:
            List of repository URLs (pre-filtered)
        """
        if source == "well_structured":
            finder = WellStructuredRepoFinder()
            repos = finder.find_well_structured_repos(min_stars=min_stars, limit=limit)
        else:
            # Fetch from GitHub
            repo_infos = fetch_repositories(
                source="github",
                min_stars=min_stars,
                limit=limit * 2  # Fetch more, will filter
            )
            repos = [repo.url for repo in repo_infos]
        
        # Pre-filter (with progress logging)
        candidates = []
        total_repos = len(repos)
        
        logger.info("Starting pre-filtering", total=total_repos, target=limit)
        
        # Handle empty repos list
        if total_repos == 0:
            logger.warning("No repositories fetched", source=source, min_stars=min_stars)
            return []
        
        i = 0  # Initialize i for the case where loop doesn't execute
        for i, repo_url in enumerate(repos, 1):
            # Skip if already reviewed
            if repo_url in self.reviewed_repos["kept"] or repo_url in self.reviewed_repos["discarded"]:
                logger.debug("Skipping already reviewed", url=repo_url)
                continue
            
            # Log progress every 10 repos
            if i % 10 == 0 or i == 1:
                logger.info("Pre-filtering progress", 
                          current=i, 
                          total=total_repos, 
                          candidates=len(candidates),
                          progress=f"{i/total_repos*100:.1f}%")
            
            try:
                should_review, reason = self.pre_filter_repo(repo_url)
                if should_review:
                    candidates.append(repo_url)
                    logger.info("✅ Candidate repository", 
                              url=repo_url, 
                              candidates=len(candidates),
                              progress=f"{i}/{total_repos}")
                else:
                    # Log rejection reason (use info level so we can see what's happening)
                    logger.info("Pre-filtered out", url=repo_url, reason=reason)
            except Exception as e:
                logger.warning("Error pre-filtering repository", 
                             url=repo_url, 
                             error=str(e))
                continue
            
            if len(candidates) >= limit:
                logger.info("Reached target limit", candidates=len(candidates))
                break
        
        # Calculate stats (handle case where no repos were checked)
        total_checked = i if i > 0 else total_repos
        pass_rate = f"{len(candidates)/total_checked*100:.1f}%" if total_checked > 0 else "0.0%"
        
        logger.info("Pre-filtering complete", 
                   total_checked=total_checked,
                   candidates=len(candidates),
                   pass_rate=pass_rate)
        return candidates

