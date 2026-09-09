import json
import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from .config import (
    resolve_table_name,
    DEFAULT_TABLE,
    PROJECT_TABLE,
    DEFAULT_LIMIT,
    DEFAULT_MIN_SCORE,
)
from .db import get_table
from .embedder import get_embedding

def resolve_taxonomy_category(raw_category: str = "", metadata: Dict[str, Any] = None) -> str:
    """
    Map raw category and metadata into the 3-category taxonomy:
    procedural, declarative, episodic.
    """
    metadata = metadata or {}
    if "memory_type" in metadata:
        mt = str(metadata["memory_type"]).strip().lower()
        if mt in ("procedural", "declarative", "episodic"):
            return mt

    cat = str(raw_category or "").strip().lower()
    if cat in ("procedural", "learned-instinct", "best-practice", "pattern", "agent-tip"):
        return "procedural"
    if cat in ("episodic", "error-handling", "bug-fix", "workaround", "troubleshooting"):
        return "episodic"
    return "declarative"

def compute_trust_score(category_type: str, metadata: Dict[str, Any] = None) -> float:
    """
    Compute trust score based on taxonomy and metadata:
    - Procedural: CLv2 confidence (0.7 to 0.95)
    - Declarative: 1.0 (durable architectural invariants)
    - Episodic: 0.5 if unconfirmed (1st sighting), 1.0 if confirmed
    """
    metadata = metadata or {}
    if category_type == "procedural":
        conf = metadata.get("confidence")
        if isinstance(conf, (int, float)):
            return round(min(1.0, max(0.1, float(conf))), 4)
        return 0.85
    if category_type == "episodic":
        return 0.5 if metadata.get("trust_state") == "unconfirmed" else 1.0
    return 1.0

def compute_freshness_weight(category_type: str, date_str: str | None, half_life_days: float = 30.0) -> float:
    """
    Compute category-specific freshness weight:
    - Declarative: flat 1.0
    - Procedural: flat 1.0 (decay handled natively by CLv2 confidence lifecycle)
    - Episodic: steep exponential temporal decay with 30-day half-life
    """
    if category_type in ("declarative", "procedural"):
        return 1.0

    if not date_str:
        return 1.0

    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta_days = max(0.0, (now - dt).total_seconds() / 86400.0)
        decay_lambda = math.log(2.0) / half_life_days
        freshness = math.exp(-decay_lambda * delta_days)
        return round(min(1.0, max(0.1, freshness)), 4)
    except Exception:
        return 1.0

def search(
    query: str,
    table: str = DEFAULT_TABLE,
    limit: int = DEFAULT_LIMIT,
    category: Optional[str] = None,
    min_score: float = DEFAULT_MIN_SCORE,
) -> List[Dict[str, Any]]:
    """
    Execute semantic vector search with Trust and Freshness ranking.
    Formula: Rank Score = Cosine Similarity * Trust Score * Freshness Weight
    """
    if not query or not isinstance(query, str) or not query.strip():
        raise ValueError('A valid non-empty "query" string is required.')

    query_str = query.strip()
    query_vector = get_embedding(query_str)

    target_tables = (
        [PROJECT_TABLE, DEFAULT_TABLE]
        if table in ("all", "both")
        else [resolve_table_name(table)]
    )

    all_results = []

    for table_name in target_tables:
        try:
            tbl = get_table(table_name)
            if tbl.count_rows() == 0:
                continue

            search_query = tbl.search(query_vector).metric("cosine").limit(limit * 2)

            if category and category.strip():
                escaped_cat = category.strip().replace("'", "''")
                search_query = search_query.where(f"category = '{escaped_cat}'")

            rows = search_query.to_list()

            for row in rows:
                distance = float(row.get("_distance", 1.0))
                similarity = round(max(0.0, 1.0 - distance), 4)

                raw_meta = row.get("metadata", "{}")
                try:
                    parsed_meta = json.loads(raw_meta) if isinstance(raw_meta, str) else (raw_meta or {})
                except Exception:
                    parsed_meta = {"raw": raw_meta}

                raw_category = row.get("category", "")
                memory_type = resolve_taxonomy_category(raw_category, parsed_meta)
                trust_score = compute_trust_score(memory_type, parsed_meta)
                date_ref = row.get("updatedAt") or row.get("createdAt")
                freshness_weight = compute_freshness_weight(memory_type, date_ref)

                rank_score = round(similarity * trust_score * freshness_weight, 4)

                if rank_score < min_score:
                    continue

                all_results.append({
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "content": row.get("content"),
                    "category": raw_category,
                    "memory_type": memory_type,
                    "metadata": parsed_meta,
                    "similarity": similarity,
                    "trust_score": trust_score,
                    "freshness_weight": freshness_weight,
                    "rank_score": rank_score,
                    "score": rank_score,
                    "distance": round(distance, 4),
                    "table": table_name,
                    "updatedAt": row.get("updatedAt"),
                })
        except Exception as err:
            import sys
            print(f"[Warning] Error searching table '{table_name}': {err}", file=sys.stderr)

    all_results.sort(key=lambda r: r["rank_score"], reverse=True)
    return all_results[:limit]
