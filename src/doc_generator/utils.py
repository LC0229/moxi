"""Utility functions for document generation."""

from pathlib import Path
from typing import Optional, List

logger = None  # Will be initialized when needed


def read_project_metadata(repo_path: Path) -> dict:
    """
    Read project metadata from pyproject.toml, package.json, or setup.py.
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Dictionary with project metadata (name, description, version, etc.)
    """
    metadata = {
        "name": None,
        "description": None,
        "version": None,
        "author": None,
        "license": None,
    }
    
    # Try pyproject.toml (Python projects)
    pyproject_path = repo_path / "pyproject.toml"
    if pyproject_path.exists():
        try:
            import tomli  # Python 3.11+ has tomllib, but tomli is more compatible
            with open(pyproject_path, "rb") as f:
                data = tomli.load(f)
            
            if "project" in data:
                project = data["project"]
                metadata["name"] = project.get("name")
                metadata["description"] = project.get("description")
                if "authors" in project and project["authors"]:
                    if isinstance(project["authors"][0], dict):
                        metadata["author"] = project["authors"][0].get("name")
                    else:
                        metadata["author"] = project["authors"][0]
                metadata["license"] = project.get("license", {}).get("text") if isinstance(project.get("license"), dict) else project.get("license")
            
            if "tool" in data and "poetry" in data["tool"]:
                poetry = data["tool"]["poetry"]
                if not metadata["name"]:
                    metadata["name"] = poetry.get("name")
                if not metadata["description"]:
                    metadata["description"] = poetry.get("description")
                if not metadata["version"]:
                    metadata["version"] = poetry.get("version")
        except ImportError:
            # Fallback: simple parsing without tomli
            try:
                content = pyproject_path.read_text(encoding="utf-8")
                # Simple regex-based extraction
                import re
                name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if name_match:
                    metadata["name"] = name_match.group(1)
                desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
                if desc_match:
                    metadata["description"] = desc_match.group(1)
            except Exception:
                pass
        except Exception:
            pass
    
    # Try package.json (Node.js projects)
    package_json_path = repo_path / "package.json"
    if package_json_path.exists():
        try:
            import json
            with open(package_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not metadata["name"]:
                metadata["name"] = data.get("name")
            if not metadata["description"]:
                metadata["description"] = data.get("description")
            if not metadata["version"]:
                metadata["version"] = data.get("version")
            if not metadata["author"]:
                metadata["author"] = data.get("author")
            if not metadata["license"]:
                metadata["license"] = data.get("license")
        except Exception:
            pass
    
    return metadata


def read_key_file_content(repo_path: Path, file_path: Path, max_lines: int = 50) -> Optional[str]:
    """
    Read content from a key file (limited to avoid token limits).
    
    Args:
        repo_path: Repository root path
        file_path: Path to file (relative to repo_path or absolute)
        max_lines: Maximum number of lines to read
        
    Returns:
        File content (first max_lines lines) or None if file doesn't exist
    """
    try:
        if file_path.is_absolute():
            full_path = file_path
        else:
            full_path = repo_path / file_path
        
        if not full_path.exists() or not full_path.is_file():
            return None
        
        # Read first max_lines
        lines = []
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
        
        content = "".join(lines)
        if len(lines) == max_lines:
            content += f"\n... (truncated, showing first {max_lines} lines)"
        
        return content
    except Exception:
        return None


def format_file_tree(all_files: List[Path], max_depth: int = 3, max_files: int = 100) -> str:
    """
    Format a list of file paths into a tree structure.
    
    Args:
        all_files: List of file paths (relative to repo root)
        max_depth: Maximum depth to show in tree
        max_files: Maximum number of files to include
        
    Returns:
        Formatted tree string
    """
    if not all_files:
        return "No files found"
    
    # Filter and sort files
    filtered_files = []
    for file_path in all_files:
        # Skip hidden files and common ignore patterns
        parts = file_path.parts
        if any(part.startswith('.') and part != '.env.example' for part in parts):
            continue
        if '__pycache__' in parts or '.git' in parts:
            continue
        if len(parts) > max_depth:
            continue
        filtered_files.append(file_path)
    
    # Limit number of files
    filtered_files = sorted(filtered_files)[:max_files]
    
    # Build tree structure
    tree_lines = []
    seen_dirs = set()
    
    for file_path in filtered_files:
        parts = file_path.parts
        indent = ""
        
        # Build directory structure
        for i, part in enumerate(parts[:-1]):
            dir_path = Path(*parts[:i+1])
            if dir_path not in seen_dirs:
                prefix = "├── " if i == 0 else "│   " * i + "├── "
                tree_lines.append(f"{prefix}{part}/")
                seen_dirs.add(dir_path)
        
        # Add file
        if len(parts) == 1:
            prefix = ""
        else:
            prefix = "│   " * (len(parts) - 1)
        prefix += "└── " if file_path == filtered_files[-1] or not any(
            f.parts[:len(parts)-1] == parts[:-1] and f != file_path 
            for f in filtered_files[filtered_files.index(file_path)+1:]
        ) else "├── "
        
        tree_lines.append(f"{prefix}{parts[-1]}")
    
    return "\n".join(tree_lines)
