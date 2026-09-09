import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import CANDIDATES_FILE, PROJECT_TABLE, resolve_table_name
from .save import save

def get_candidates_file_path() -> Path:
    return CANDIDATES_FILE

def load_candidates() -> List[Dict[str, Any]]:
    """Load all provisional candidates from disk."""
    path = get_candidates_file_path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as err:
        import sys
        print(f"[Warning] Failed reading provisional candidates: {err}", file=sys.stderr)
        return []

def save_candidates(candidates: List[Dict[str, Any]]) -> None:
    """Save candidates list to disk."""
    path = get_candidates_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)

def generate_candidate_id(title: str = "") -> str:
    """Generate a clean slug candidate ID."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]
    return f"cand-{slug or int(datetime.now().timestamp())}"

def record_candidate(
    title: str,
    content: str,
    category: str = "episodic",
    domain: str = "error-handling",
    table: str = PROJECT_TABLE,
    metadata: Optional[Dict[str, Any]] = None,
    candidate_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record a technical/episodic candidate solution through the Provisional Gate.
    - 1st sighting: Staged as 'unconfirmed' (held at gate, not written to LanceDB).
    - 2nd sighting: Automatically promoted to LanceDB as 'confirmed' episodic memory.
    """
    if not title or not content:
        raise ValueError('Candidate requires both "title" and "content".')

    candidates = load_candidates()
    target_id = candidate_id.strip() if candidate_id else generate_candidate_id(title)

    # Search for existing candidate by ID or exact title
    existing_idx = -1
    for idx, c in enumerate(candidates):
        if c.get("id") == target_id or c.get("title", "").strip().lower() == title.strip().lower():
            existing_idx = idx
            break

    now_iso = datetime.now(timezone.utc).isoformat()
    meta = metadata or {}

    if existing_idx == -1:
        # 1st sighting: stage as unconfirmed
        new_candidate = {
            "id": target_id,
            "title": title.strip(),
            "content": content.strip(),
            "category": category,
            "domain": domain,
            "target_table": resolve_table_name(table),
            "trust_state": "unconfirmed",
            "reinforcement_count": 1,
            "sightings": [now_iso],
            "metadata": meta,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        candidates.append(new_candidate)
        save_candidates(candidates)

        return {
            "status": "staged",
            "promoted": False,
            "candidate": new_candidate,
            "message": f"[Trust Gate] 1st sighting: Staged as UNCONFIRMED. Held at gate (not written to LanceDB).",
        }

    # 2nd or further sighting: promote to LanceDB!
    candidate = candidates[existing_idx]
    candidate["reinforcement_count"] = candidate.get("reinforcement_count", 1) + 1
    candidate["sightings"].append(now_iso)
    candidate["updated_at"] = now_iso
    candidate["trust_state"] = "confirmed"

    promoted_meta = {
        **meta,
        **candidate.get("metadata", {}),
        "memory_type": "episodic",
        "trust_state": "confirmed",
        "reinforcement_count": candidate["reinforcement_count"],
        "source": "provisional-gate",
        "candidate_id": candidate["id"],
    }

    target_table = candidate.get("target_table") or resolve_table_name(table)
    db_result = save(
        title=candidate["title"],
        content=candidate["content"],
        table=target_table,
        category=candidate.get("category", "episodic"),
        metadata=promoted_meta,
        id=candidate["id"],
    )

    candidate["promoted_at"] = now_iso
    candidate["promoted_table"] = target_table
    save_candidates(candidates)

    return {
        "status": "promoted",
        "promoted": True,
        "candidate": candidate,
        "db_record": db_result,
        "message": f"[Trust Gate: PROMOTED] {candidate['reinforcement_count']}nd sighting reinforced! Promoted to LanceDB ({target_table}) as fully confirmed episodic memory.",
    }

def confirm_candidate(candidate_id: str, table: Optional[str] = None) -> Dict[str, Any]:
    """Manually confirm and promote a staged candidate."""
    candidates = load_candidates()
    candidate = next((c for c in candidates if c.get("id") == candidate_id), None)

    if not candidate:
        raise ValueError(f"No staged candidate found with ID '{candidate_id}'.")

    target_table = resolve_table_name(table or candidate.get("target_table") or PROJECT_TABLE)
    now_iso = datetime.now(timezone.utc).isoformat()

    candidate["trust_state"] = "confirmed"
    candidate["promoted_at"] = now_iso
    candidate["promoted_table"] = target_table

    promoted_meta = {
        **candidate.get("metadata", {}),
        "memory_type": "episodic",
        "trust_state": "confirmed",
        "source": "manual-gate-confirmation",
        "candidate_id": candidate["id"],
    }

    db_result = save(
        title=candidate["title"],
        content=candidate["content"],
        table=target_table,
        category=candidate.get("category", "episodic"),
        metadata=promoted_meta,
        id=candidate["id"],
    )

    save_candidates(candidates)

    return {
        "status": "promoted",
        "promoted": True,
        "candidate": candidate,
        "db_record": db_result,
        "message": f"[Trust Gate: CONFIRMED] Candidate '{candidate_id}' manually promoted to LanceDB ({target_table}).",
    }
