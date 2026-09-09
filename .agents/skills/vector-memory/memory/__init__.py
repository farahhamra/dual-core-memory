"""
Dual-Core Vector Memory Subsystem (Python)
Embeddings via local Ollama (nomic-embed-text) + Storage via LanceDB
"""

from .config import CONFIG, STORAGE_PATH, DEFAULT_TABLE, PROJECT_TABLE
from .db import get_table, get_table_stats, get_database, initialize_tables
from .embedder import get_embedding, get_batch_embeddings
from .search import search, resolve_taxonomy_category, compute_trust_score, compute_freshness_weight
from .save import save
from .candidate_gate import record_candidate, confirm_candidate, load_candidates
from .sync_instincts import sync_instincts

__all__ = [
    "CONFIG",
    "STORAGE_PATH",
    "DEFAULT_TABLE",
    "PROJECT_TABLE",
    "get_table",
    "get_table_stats",
    "get_database",
    "initialize_tables",
    "get_embedding",
    "get_batch_embeddings",
    "search",
    "resolve_taxonomy_category",
    "compute_trust_score",
    "compute_freshness_weight",
    "save",
    "record_candidate",
    "confirm_candidate",
    "load_candidates",
    "sync_instincts",
]
