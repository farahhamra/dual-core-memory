import os
from typing import List, Dict, Any
import lancedb
import pyarrow as pa
from .config import STORAGE_PATH, DEFAULT_TABLE, PROJECT_TABLE, EMBEDDING_DIMENSION, resolve_table_name

# Global database connection cache
_db_instance = None

def get_schema() -> pa.Schema:
    """Return PyArrow schema matching LanceDB vector memory records."""
    return pa.schema([
        pa.field("id", pa.string(), nullable=False),
        pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIMENSION), nullable=False),
        pa.field("title", pa.string(), nullable=False),
        pa.field("content", pa.string(), nullable=False),
        pa.field("category", pa.string(), nullable=False),
        pa.field("metadata", pa.string(), nullable=False),
        pa.field("createdAt", pa.string(), nullable=False),
        pa.field("updatedAt", pa.string(), nullable=False),
    ])

def get_database():
    """Get or establish LanceDB connection."""
    global _db_instance
    if _db_instance is None:
        STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        _db_instance = lancedb.connect(str(STORAGE_PATH))
    return _db_instance

def get_table(name: str | None = None):
    """
    Get existing table or create a new one with the standard Arrow schema.
    """
    table_name = resolve_table_name(name)
    db = get_database()
    existing_tables = db.table_names()

    if table_name in existing_tables:
        return db.open_table(table_name)

    schema = get_schema()
    return db.create_table(table_name, schema=schema)

def initialize_tables() -> None:
    """Ensure both default and project tables exist."""
    for name in (DEFAULT_TABLE, PROJECT_TABLE):
        get_table(name)

def get_table_stats() -> List[Dict[str, Any]]:
    """Return statistics (name and row count) for all tables in the database."""
    db = get_database()
    stats = []
    for name in db.table_names():
        tbl = db.open_table(name)
        stats.append({
            "name": name,
            "count": tbl.count_rows(),
        })
    return stats
