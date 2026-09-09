import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_PATH = BASE_DIR / "data"
CANDIDATES_FILE = STORAGE_PATH / "provisional-candidates.json"

# Ollama configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
EMBEDDING_DIMENSION = 768

# Tables
DEFAULT_TABLE = "default_memory"
PROJECT_TABLE = "project_memory"

# Search defaults
DEFAULT_LIMIT = 5
DEFAULT_MIN_SCORE = 0.0

# Backward compatibility config dictionary
CONFIG = {
    "ollama": {
        "baseUrl": OLLAMA_BASE_URL,
        "model": OLLAMA_EMBED_MODEL,
        "dimension": EMBEDDING_DIMENSION,
    },
    "db": {
        "storagePath": str(STORAGE_PATH),
        "tables": {
            "default": DEFAULT_TABLE,
            "project": PROJECT_TABLE,
        },
    },
    "search": {
        "defaultLimit": DEFAULT_LIMIT,
        "minScore": DEFAULT_MIN_SCORE,
    },
}

def resolve_table_name(name: str | None) -> str:
    """Normalize and resolve friendly table names to their storage names."""
    if not name:
        return DEFAULT_TABLE
    normalized = name.strip().lower().replace("-", "_")
    if normalized in ("default", "default_memory"):
        return DEFAULT_TABLE
    if normalized in ("project", "project_memory"):
        return PROJECT_TABLE
    return normalized
