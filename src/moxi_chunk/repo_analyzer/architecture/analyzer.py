"""Architecture analyzer using deep code analysis (not just keywords)."""

import ast
import re
from typing import Dict, List, Set, Tuple

from core import get_logger
from moxi_chunk.repo_analyzer.models import RepositoryInfo

logger = get_logger(__name__)


def analyze_architecture_with_rules(repo_analysis: RepositoryInfo) -> Dict:
    """
    Analyze architecture by actually understanding code structure.
    
    This function:
    1. Parses Python files to understand actual code structure
    2. Analyzes imports, class definitions, decorators, function calls
    3. Detects components based on actual code patterns, not just keywords
    4. Builds connections based on actual import relationships
    
    Args:
        repo_analysis: Repository analysis information
        
    Returns:
        Dictionary with components and connections
    """
    components = []
    connections = []
    
    # Analyze each Python file individually to understand its role
    file_analyses = []
    for file_path in repo_analysis.all_files:
        if file_path.suffix == ".py":
            analysis = _analyze_file_deep(repo_analysis.path, file_path)
            if analysis:
                file_analyses.append(analysis)
    
    # Aggregate findings from all files
    api_files = []
    db_files = []
    service_files = []
    model_files = []
    cache_files = []
    queue_files = []
    
    for file_analysis in file_analyses:
        file_type = file_analysis.get('type')
        file_path = file_analysis.get('path')
        
        if file_type == 'api_server':
            api_files.append(file_analysis)
        elif file_type == 'database':
            db_files.append(file_analysis)
        elif file_type == 'service':
            service_files.append(file_analysis)
        elif file_type == 'model':
            model_files.append(file_analysis)
        elif file_type == 'cache':
            cache_files.append(file_analysis)
        elif file_type == 'queue':
            queue_files.append(file_analysis)
        
        # Extract connections from imports
        for imp in file_analysis.get('imports', []):
            target_type = _classify_import_target(imp, file_analyses)
            if target_type and file_type:
                connections.append({
                    "from": file_type,
                    "to": target_type,
                    "confidence": 0.9
                })
    
    # Build components based on actual findings
    if api_files:
        components.append({
            "name": "API Server",
            "type": "server",
            "layer": "frontend",
            "confidence": 1.0,
            "evidence": f"Found {len(api_files)} API files with route decorators"
        })
    
    if db_files or model_files:
        db_type = _detect_database_from_code(db_files + model_files)
        components.append({
            "name": db_type,
            "type": "database",
            "layer": "data",
            "confidence": 1.0,
            "evidence": f"Found {len(db_files)} DB files, {len(model_files)} model files"
        })
    
    if service_files:
        components.append({
            "name": "Business Logic",
            "type": "application",
            "layer": "middle",
            "confidence": 1.0,
            "evidence": f"Found {len(service_files)} service files"
        })
    
    if cache_files:
        components.append({
            "name": "Cache",
            "type": "cache",
            "layer": "data",
            "confidence": 1.0,
            "evidence": f"Found {len(cache_files)} cache files"
        })
    
    if queue_files:
        components.append({
            "name": "Message Queue",
            "type": "queue",
            "layer": "middle",
            "confidence": 1.0,
            "evidence": f"Found {len(queue_files)} queue files"
        })
        components.append({
            "name": "Worker",
            "type": "worker",
            "layer": "middle",
            "confidence": 0.8
        })
    
    # If no components found, it's likely a simple tool/library
    return {
        "components": components,
        "connections": connections,
        "structure": str(repo_analysis.path)
    }


def _analyze_file_deep(repo_path, file_path) -> Dict:
    """
    Deep analysis of a single Python file.
    
    Analyzes:
    - AST to understand code structure
    - Decorators (like @app.route, @router.get)
    - Class definitions (like SQLAlchemy models)
    - Import statements
    - Function definitions and calls
    
    Returns:
        Dict with file type, imports, and evidence
    """
    try:
        full_path = repo_path / file_path
        if not full_path.exists():
            return None
        
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        
        # Try to parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # If AST parsing fails, fall back to regex analysis
            return _analyze_file_regex(content, file_path)
        
        file_type = None
        imports = []
        evidence = []
        
        # Analyze AST nodes
        for node in ast.walk(tree):
            # Extract imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
            
            # Check for API route decorators
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    decorator_str = _ast_to_string(decorator)
                    if _is_api_decorator(decorator_str):
                        file_type = 'api_server'
                        evidence.append(f"Found API decorator: {decorator_str}")
            
            # Check for SQLAlchemy models
            if isinstance(node, ast.ClassDef):
                # Check if class inherits from SQLAlchemy Base
                for base in node.bases:
                    base_str = _ast_to_string(base)
                    if 'Base' in base_str or 'db.Model' in base_str or 'DeclarativeBase' in base_str:
                        file_type = 'model'
                        evidence.append(f"Found model class: {node.name}")
                
                # Check for SQLAlchemy Column definitions
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            target_str = _ast_to_string(target)
                            if 'Column' in content or 'relationship' in content:
                                if file_type != 'model':
                                    file_type = 'model'
                                    evidence.append(f"Found SQLAlchemy Column in {node.name}")
            
            # Check for database connections
            if isinstance(node, ast.Call):
                call_str = _ast_to_string(node)
                if _is_database_call(call_str, content):
                    if not file_type:
                        file_type = 'database'
                    evidence.append(f"Found database connection: {call_str}")
            
            # Check for cache usage
            if isinstance(node, (ast.Call, ast.Attribute)):
                node_str = _ast_to_string(node)
                if _is_cache_usage(node_str):
                    if not file_type:
                        file_type = 'cache'
                    evidence.append(f"Found cache usage: {node_str}")
        
        # If no type detected from AST, try regex fallback
        if not file_type:
            regex_result = _analyze_file_regex(content, file_path)
            if regex_result:
                file_type = regex_result.get('type')
                evidence.extend(regex_result.get('evidence', []))
        
        if file_type:
            return {
                "path": str(file_path),
                "type": file_type,
                "imports": imports,
                "evidence": evidence
            }
        
        return None
        
    except Exception as e:
        logger.debug("Error analyzing file", file=str(file_path), error=str(e))
        return None


def _analyze_file_regex(content: str, file_path) -> Dict:
    """Fallback: Analyze file using regex patterns when AST parsing fails."""
    file_type = None
    evidence = []
    
    # Check for API route patterns
    api_patterns = [
        r'@app\.route\s*\(',  # Flask
        r'@router\.(get|post|put|delete)\s*\(',  # FastAPI
        r'@.*\.route\s*\(',  # Generic route decorator
        r'Blueprint\s*\(',  # Flask Blueprint
        r'APIRouter\s*\(',  # FastAPI Router
    ]
    for pattern in api_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            file_type = 'api_server'
            evidence.append(f"Found API route pattern: {pattern}")
            break
    
    # Check for SQLAlchemy models
    if re.search(r'class\s+\w+.*\(.*Base.*\)', content) or \
       re.search(r'class\s+\w+.*\(.*db\.Model.*\)', content) or \
       re.search(r'Column\s*\(', content):
        file_type = 'model'
        evidence.append("Found SQLAlchemy model pattern")
    
    # Check for database connections
    db_patterns = [
        r'create_engine\s*\(',
        r'connect\s*\(',
        r'sessionmaker\s*\(',
        r'engine\.connect\s*\(',
    ]
    for pattern in db_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            if not file_type:
                file_type = 'database'
            evidence.append(f"Found database pattern: {pattern}")
    
    # Check for service patterns
    service_patterns = [
        r'class\s+\w+Service',
        r'def\s+\w+_service\s*\(',
        r'class\s+\w+.*Service.*:',
    ]
    for pattern in service_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            if not file_type:
                file_type = 'service'
            evidence.append(f"Found service pattern: {pattern}")
    
    # Check for cache
    if re.search(r'redis\.|cache\.|Cache\(', content, re.IGNORECASE):
        if not file_type:
            file_type = 'cache'
        evidence.append("Found cache usage")
    
    # Check for queue
    if re.search(r'celery\.|rabbitmq|pika\.|Queue\(', content, re.IGNORECASE):
        if not file_type:
            file_type = 'queue'
        evidence.append("Found queue usage")
    
    if file_type:
        return {"type": file_type, "evidence": evidence}
    return None


def _ast_to_string(node) -> str:
    """Convert AST node to string representation."""
    try:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{_ast_to_string(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            func_str = _ast_to_string(node.func)
            return func_str
        else:
            return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
    except:
        return str(node)


def _is_api_decorator(decorator_str: str) -> bool:
    """Check if decorator is an API route decorator."""
    api_patterns = [
        'route', 'get', 'post', 'put', 'delete', 'patch',
        'blueprint', 'router', 'endpoint'
    ]
    return any(pattern in decorator_str.lower() for pattern in api_patterns)


def _is_database_call(call_str: str, content: str) -> bool:
    """Check if call is a database connection."""
    db_keywords = ['create_engine', 'connect', 'session', 'engine']
    return any(keyword in call_str.lower() for keyword in db_keywords)


def _is_cache_usage(node_str: str) -> bool:
    """Check if node is cache usage."""
    cache_keywords = ['redis', 'cache', 'get', 'set']
    return any(keyword in node_str.lower() for keyword in cache_keywords)


def _classify_import_target(import_str: str, all_file_analyses: List[Dict]) -> str:
    """Classify what type of component an import refers to."""
    import_lower = import_str.lower()
    
    # Check if import matches known patterns
    if any(x in import_lower for x in ['flask', 'fastapi', 'django', 'tornado']):
        return 'api_server'
    elif any(x in import_lower for x in ['sqlalchemy', 'psycopg2', 'mysql', 'pymongo']):
        return 'database'
    elif any(x in import_lower for x in ['redis', 'cache']):
        return 'cache'
    elif any(x in import_lower for x in ['celery', 'rabbitmq', 'pika']):
        return 'queue'
    
    # Check if import is from another file in the project
    for file_analysis in all_file_analyses:
        file_path = file_analysis.get('path', '')
        if import_str in file_path or file_path.replace('/', '.').replace('\\', '.') in import_str:
            return file_analysis.get('type')
    
    return None


def _detect_database_from_code(db_files: List[Dict]) -> str:
    """Detect specific database type from code analysis."""
    # This would analyze the actual code in db_files to determine database type
    # For now, return generic "Database"
    return "Database"


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

