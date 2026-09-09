import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .config import resolve_table_name, PROJECT_TABLE
from .db import get_table
from .embedder import get_embedding

def save(
    title: str,
    content: str,
    table: str = PROJECT_TABLE,
    category: str = "general",
    metadata: Optional[Dict[str, Any] | str] = None,
    id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Save or upsert a memory record into the specified LanceDB table.
    Generates a 768-dim float vector from title and content.
    """
    if not title or not isinstance(title, str) or not title.strip():
        raise ValueError('A valid non-empty "title" is required to save a memory.')
    if not content or not isinstance(content, str) or not content.strip():
        raise ValueError('A valid non-empty "content" string is required to save a memory.')

    table_name = resolve_table_name(table)
    tbl = get_table(table_name)

    record_id = id.strip() if id and isinstance(id, str) and id.strip() else str(uuid.uuid4())

    # Generate vector embedding for semantic search
    text_to_embed = f"{title.strip()}\n\n{content.strip()}"
    vector = get_embedding(text_to_embed)

    # Serialize metadata
    if isinstance(metadata, str):
        meta_str = metadata
        parsed_meta = {}
        try:
            parsed_meta = json.loads(metadata)
        except Exception:
            parsed_meta = {"raw": metadata}
    elif isinstance(metadata, dict):
        meta_str = json.dumps(metadata)
        parsed_meta = metadata
    else:
        meta_str = "{}"
        parsed_meta = {}

    now_iso = datetime.now(timezone.utc).isoformat()

    # Upsert: remove existing record with same ID if present
    try:
        escaped_id = record_id.replace("'", "''")
        tbl.delete(f"id = '{escaped_id}'")
    except Exception:
        pass

    record = {
        "id": record_id,
        "vector": vector,
        "title": title.strip(),
        "content": content.strip(),
        "category": (category or "general").strip(),
        "metadata": meta_str,
        "createdAt": now_iso,
        "updatedAt": now_iso,
    }

    tbl.add([record])

    return {
        "success": True,
        "id": record_id,
        "table": table_name,
        "title": record["title"],
        "category": record["category"],
        "metadata": parsed_meta,
        "updatedAt": now_iso,
    }
