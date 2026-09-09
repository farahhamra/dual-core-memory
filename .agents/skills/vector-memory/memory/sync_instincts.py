import os
import re
from pathlib import Path
from typing import Dict, Any, List
from .config import PROJECT_TABLE
from .save import save

CONFIDENCE_THRESHOLD = 0.70

def get_homunculus_dir() -> Path:
    """Find the ECC homunculus directory across Windows / Linux / macOS."""
    env_dir = os.environ.get("HOMUNCULUS_DIR")
    if env_dir:
        return Path(env_dir)

    home = Path.home()
    # Check XDG / standard local share path
    candidate = home / ".local" / "share" / "ecc-homunculus"
    if candidate.exists():
        return candidate

    # Windows AppData path
    appdata = os.environ.get("LOCALAPPDATA")
    if appdata:
        cand2 = Path(appdata) / "ecc-homunculus"
        if cand2.exists():
            return cand2

    return candidate

def parse_simple_yaml_frontmatter(content: str) -> Dict[str, Any]:
    """
    Parse basic YAML frontmatter without external pyyaml dependency.
    """
    data: Dict[str, Any] = {}
    lines = content.splitlines()

    in_frontmatter = False
    fm_lines = []

    for line in lines:
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                in_frontmatter = False
                break
        if in_frontmatter:
            fm_lines.append(line)

    for line in fm_lines:
        if ":" in line:
            key, val = line.split(":", 1)
            k = key.strip()
            v = val.strip().strip("\"'")
            try:
                if "." in v:
                    data[k] = float(v)
                else:
                    data[k] = int(v)
            except ValueError:
                data[k] = v

    return data

def sync_instincts(threshold: float = CONFIDENCE_THRESHOLD, table: str = PROJECT_TABLE) -> Dict[str, Any]:
    """
    Evaluate instincts in homunculus and promote those meeting the confidence threshold.
    """
    homunculus_dir = get_homunculus_dir()
    instincts_dir = homunculus_dir / "instincts" / "personal"

    results = {
        "homunculus_dir": str(homunculus_dir),
        "threshold": threshold,
        "scanned": 0,
        "promoted": 0,
        "held": 0,
        "details": [],
    }

    if not instincts_dir.exists():
        results["message"] = f"Instincts directory does not exist: {instincts_dir}"
        return results

    yaml_files = list(instincts_dir.glob("*.yaml")) + list(instincts_dir.glob("*.yml"))
    results["scanned"] = len(yaml_files)

    for yf in yaml_files:
        try:
            content = yf.read_text(encoding="utf-8")
            meta = parse_simple_yaml_frontmatter(content)
            confidence = float(meta.get("confidence", 0.5))
            instinct_id = meta.get("id") or yf.stem
            title = meta.get("name") or meta.get("trigger") or instinct_id

            if confidence >= threshold:
                save(
                    title=f"Instinct: {title}",
                    content=content,
                    table=table,
                    category="procedural",
                    metadata={
                        "memory_type": "procedural",
                        "confidence": confidence,
                        "source": "clv2-instinct",
                        "instinct_id": instinct_id,
                        "file": yf.name,
                    },
                    id=f"instinct-{instinct_id}",
                )
                results["promoted"] += 1
                results["details"].append({
                    "id": instinct_id,
                    "confidence": confidence,
                    "status": "promoted",
                })
            else:
                results["held"] += 1
                results["details"].append({
                    "id": instinct_id,
                    "confidence": confidence,
                    "status": "held",
                })
        except Exception as err:
            results["details"].append({
                "file": yf.name,
                "status": "error",
                "error": str(err),
            })

    return results
