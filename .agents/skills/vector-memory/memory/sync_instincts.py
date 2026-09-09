import os
import re
from pathlib import Path
from typing import Dict, Any, List
from .config import PROJECT_TABLE
from .save import save

CONFIDENCE_THRESHOLD = 0.70

def get_homunculus_dir(auto_create: bool = True) -> Path:
    """Find and optionally initialize the ECC homunculus directory across Windows / Linux / macOS."""
    env_dir = os.environ.get("CLV2_HOMUNCULUS_DIR") or os.environ.get("HOMUNCULUS_DIR")
    if env_dir:
        res = Path(env_dir)
    else:
        # Windows AppData path
        appdata = os.environ.get("LOCALAPPDATA")
        if appdata:
            res = Path(appdata) / "ecc-homunculus"
        else:
            xdg = os.environ.get("XDG_DATA_HOME")
            if xdg:
                res = Path(xdg) / "ecc-homunculus"
            else:
                res = Path.home() / ".local" / "share" / "ecc-homunculus"

    if auto_create:
        (res / "instincts" / "personal").mkdir(parents=True, exist_ok=True)
        (res / "projects").mkdir(parents=True, exist_ok=True)

    return res

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
    Evaluate instincts in homunculus (both global and project-scoped) and promote those meeting the confidence threshold.
    """
    homunculus_dir = get_homunculus_dir(auto_create=True)
    global_dir = homunculus_dir / "instincts" / "personal"
    projects_dir = homunculus_dir / "projects"

    results = {
        "homunculus_dir": str(homunculus_dir),
        "threshold": threshold,
        "scanned": 0,
        "promoted": 0,
        "held": 0,
        "details": [],
    }

    # Discover all candidate yaml files from global and project scopes
    yaml_files: List[Path] = []
    if global_dir.exists():
        yaml_files.extend(list(global_dir.glob("*.yaml")) + list(global_dir.glob("*.yml")))

    if projects_dir.exists():
        yaml_files.extend(list(projects_dir.glob("*/instincts/personal/*.yaml")) + list(projects_dir.glob("*/instincts/personal/*.yml")))

    results["scanned"] = len(yaml_files)

    for yf in yaml_files:
        try:
            content = yf.read_text(encoding="utf-8")
            meta = parse_simple_yaml_frontmatter(content)
            confidence = float(meta.get("confidence", 0.5))
            instinct_id = meta.get("id") or yf.stem
            title = meta.get("name") or meta.get("trigger") or instinct_id
            scope = meta.get("scope", "global" if "projects" not in str(yf).replace("\\", "/") else "project")
            project_id = meta.get("project_id", "")
            reinforcement_count = int(meta.get("reinforcement_count", 1))

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
                        "scope": scope,
                        "project_id": project_id,
                        "reinforcement_count": reinforcement_count,
                        "file": yf.name,
                    },
                    id=f"instinct-{instinct_id}",
                )
                results["promoted"] += 1
                results["details"].append({
                    "id": instinct_id,
                    "confidence": confidence,
                    "scope": scope,
                    "status": "promoted",
                })
            else:
                results["held"] += 1
                results["details"].append({
                    "id": instinct_id,
                    "confidence": confidence,
                    "scope": scope,
                    "status": "held",
                })
        except Exception as err:
            results["details"].append({
                "file": yf.name,
                "status": "error",
                "error": str(err),
            })

    return results
