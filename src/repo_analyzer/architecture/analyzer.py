"""Architecture analyzer using rule-based detection (accurate)."""

from typing import Dict, List

from core import get_logger
from repo_analyzer.models import RepositoryInfo

logger = get_logger(__name__)


def analyze_architecture_with_rules(repo_analysis: RepositoryInfo) -> Dict:
    """
    Analyze architecture using rule-based detection (accurate).
    
    Args:
        repo_analysis: Repository analysis information
        
    Returns:
        Dictionary with components and connections
    """
    components = []
    connections = []
    
    # Read all code files to analyze
    code_text = _read_all_code(repo_analysis)
    
    # 1. Detect components (rule-based, accurate)
    # Frontend/API Layer
    if _has_flask_or_fastapi(code_text):
        components.append({
            "name": "API Server",
            "type": "server",
            "layer": "frontend",
            "confidence": 1.0
        })
    
    if _has_web_framework(code_text):
        components.append({
            "name": "Web Server",
            "type": "server",
            "layer": "frontend",
            "confidence": 1.0
        })
    
    # Application Layer
    if _has_business_logic(code_text):
        components.append({
            "name": "Business Logic",
            "type": "application",
            "layer": "middle",
            "confidence": 1.0
        })
    
    # Data Layer
    if _has_database(code_text):
        db_type = _detect_database_type(code_text)
        components.append({
            "name": db_type,
            "type": "database",
            "layer": "data",
            "confidence": 1.0
        })
    
    if _has_cache(code_text):
        components.append({
            "name": "Cache",
            "type": "cache",
            "layer": "data",
            "confidence": 1.0
        })
    
    if _has_queue(code_text):
        components.append({
            "name": "Message Queue",
            "type": "queue",
            "layer": "middle",
            "confidence": 1.0
        })
        components.append({
            "name": "Worker",
            "type": "worker",
            "layer": "middle",
            "confidence": 1.0
        })
    
    if _has_storage(code_text):
        components.append({
            "name": "Object Storage",
            "type": "storage",
            "layer": "data",
            "confidence": 1.0
        })
    
    # 2. Detect connections (scan imports)
    for file_path in repo_analysis.all_files:
        if file_path.suffix == ".py":
            imports = _extract_imports(repo_analysis.path, file_path)
            file_component = _classify_file_type(file_path, code_text)
            
            for imp in imports:
                imp_component = _classify_import_type(imp, code_text)
                if file_component and imp_component:
                    connections.append({
                        "from": file_component,
                        "to": imp_component,
                        "confidence": 1.0
                    })
    
    # If no components detected, analyze file structure to infer components
    if not components:
        # Try to infer from file structure
        file_paths = [str(f).lower() for f in repo_analysis.all_files]
        
        # Check for main entry point
        if any("main.py" in p or "app.py" in p or "__main__.py" in p for p in file_paths):
            components.append({
                "name": "Application",
                "type": "application",
                "layer": "middle",
                "confidence": 0.7
            })
        else:
            components.append({
                "name": "Application",
                "type": "application",
                "layer": "middle",
                "confidence": 0.5
            })
        
        # Check for data files (CSV, JSON, etc.) - suggests data processing
        if any(p.endswith(('.csv', '.json', '.xml')) for p in file_paths):
            components.append({
                "name": "Data Storage",
                "type": "storage",
                "layer": "data",
                "confidence": 0.6
            })
    
    return {
        "components": components,
        "connections": connections,
        "structure": str(repo_analysis.path)
    }


def _read_all_code(repo_analysis: RepositoryInfo) -> str:
    """Read all code files and combine into text."""
    code_text = ""
    for file_path in repo_analysis.all_files:
        if file_path.suffix == ".py":
            try:
                full_path = repo_analysis.path / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    code_text += content + "\n"
            except Exception:
                continue
    return code_text


def _has_flask_or_fastapi(code_text: str) -> bool:
    """Check if code uses Flask or FastAPI."""
    keywords = ["from flask", "import flask", "Flask(", "from fastapi", "import fastapi", "FastAPI("]
    return any(keyword.lower() in code_text.lower() for keyword in keywords)


def _has_database(code_text: str) -> bool:
    """Check if code uses database."""
    keywords = ["sqlalchemy", "psycopg2", "mysql", "mongodb", "pymongo", "database", "db"]
    return any(keyword.lower() in code_text.lower() for keyword in keywords)


def _has_cache(code_text: str) -> bool:
    """Check if code uses cache."""
    keywords = ["redis", "cache", "memcached"]
    return any(keyword.lower() in code_text.lower() for keyword in keywords)


def _has_queue(code_text: str) -> bool:
    """Check if code uses message queue."""
    keywords = ["rabbitmq", "celery", "queue", "pika"]
    return any(keyword.lower() in code_text.lower() for keyword in keywords)


def _has_storage(code_text: str) -> bool:
    """Check if code uses storage."""
    keywords = ["s3", "boto3", "storage", "minio"]
    return any(keyword.lower() in code_text.lower() for keyword in keywords)


def _has_web_framework(code_text: str) -> bool:
    """Check if code uses web framework (Django, etc.)."""
    keywords = ["django", "tornado", "bottle", "cherrypy"]
    return any(keyword.lower() in code_text.lower() for keyword in keywords)


def _has_business_logic(code_text: str) -> bool:
    """Check if code has business logic layer."""
    # Look for service patterns, business logic patterns
    keywords = ["service", "business", "logic", "handler", "processor"]
    return any(keyword.lower() in code_text.lower() for keyword in keywords)


def _detect_database_type(code_text: str) -> str:
    """Detect specific database type."""
    code_lower = code_text.lower()
    if "mongodb" in code_lower or "pymongo" in code_lower:
        return "MongoDB"
    elif "postgresql" in code_lower or "psycopg2" in code_lower:
        return "PostgreSQL"
    elif "mysql" in code_lower:
        return "MySQL"
    elif "sqlite" in code_lower:
        return "SQLite"
    else:
        return "Database"


def _extract_imports(repo_path, file_path) -> List[str]:
    """Extract imports from a Python file."""
    imports = []
    try:
        full_path = repo_path / file_path
        if full_path.exists():
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("import ") or line.startswith("from "):
                    imports.append(line)
    except Exception:
        pass
    return imports


def _classify_file_type(file_path, code_text: str) -> str:
    """Classify file type based on path and content."""
    path_str = str(file_path).lower()
    
    if "route" in path_str or "api" in path_str or "endpoint" in path_str:
        return "API Server"
    elif "service" in path_str or "business" in path_str or "logic" in path_str:
        return "Business Logic"
    elif "model" in path_str or "db" in path_str or "database" in path_str:
        return "Database"
    elif "cache" in path_str or "redis" in path_str:
        return "Cache"
    elif "queue" in path_str or "worker" in path_str:
        return "Worker"
    else:
        return None


def _classify_import_type(import_line: str, code_text: str) -> str:
    """Classify import type."""
    import_lower = import_line.lower()
    
    if "flask" in import_lower or "fastapi" in import_lower:
        return "API Server"
    elif "sqlalchemy" in import_lower or "psycopg2" in import_lower or "mysql" in import_lower:
        return "Database"
    elif "redis" in import_lower:
        return "Cache"
    elif "rabbitmq" in import_lower or "celery" in import_lower or "pika" in import_lower:
        return "Queue"
    else:
        return None

