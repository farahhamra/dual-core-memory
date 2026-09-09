import os
import re
from pathlib import Path
from typing import Dict, Any, List
from .config import PROJECT_TABLE
from .save import save

CONFIDENCE_THRESHOLD = 0.70

def get_homunculus_dirs() -> List[Path]:
    """Find all candidate ECC homunculus directories across Windows / Linux / macOS."""
    candidates = []
    
    # 1. Explicit env overrides
    env_dir = os.environ.get("CLV2_HOMUNCULUS_DIR") or os.environ.get("HOMUNCULUS_DIR")
    if env_dir:
        candidates.append(Path(env_dir))

    # 2. Windows LocalAppData
    appdata = os.environ.get("LOCALAPPDATA")
    if appdata:
        candidates.append(Path(appdata) / "ecc-homunculus")

    # 3. XDG standard path
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        candidates.append(Path(xdg) / "ecc-homunculus")

    # 4. Standard ~/.local/share path
    candidates.append(Path.home() / ".local" / "share" / "ecc-homunculus")

    # Return deduplicated paths
    seen = set()
    result = []
    for c in candidates:
        norm = str(c.resolve()) if c.exists() else str(c)
        if norm not in seen:
            seen.add(norm)
            result.append(c)
    return result

def get_homunculus_dir() -> Path:
    """Find the primary ECC homunculus directory across Windows / Linux / macOS."""
    dirs = get_homunculus_dirs()
    for d in dirs:
        if d.exists():
            return d
    # If none exist, return the primary candidate and ensure it is created
    primary = dirs[0] if dirs else Path.home() / ".local" / "share" / "ecc-homunculus"
    primary.mkdir(parents=True, exist_ok=True)
    return primary

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

def discover_instinct_files(project_id: str = "") -> List[Path]:
    """
    Discover all instinct YAML/YML files across both global and project-scoped directories.
    """
    homunculus_dirs = get_homunculus_dirs()
    found_files: List[Path] = []
    seen_stems = set()

    for hdir in homunculus_dirs:
        if not hdir.exists():
            continue

        # 1. Global instincts: <homunculus>/instincts/personal
        global_personal = hdir / "instincts" / "personal"
        if global_personal.exists():
            for yf in list(global_personal.glob("*.yaml")) + list(global_personal.glob("*.yml")):
                if yf.stem not in seen_stems:
                    seen_stems.add(yf.stem)
                    found_files.append(yf)

        # 2. Project-scoped instincts: <homunculus>/projects/<pid>/instincts/personal
        projects_dir = hdir / "projects"
        if projects_dir.exists():
            if project_id:
                target_dirs = [projects_dir / project_id / "instincts" / "personal"]
            else:
                target_dirs = list(projects_dir.glob("*/instincts/personal"))

            for p_dir in target_dirs:
                if p_dir.exists():
                    for yf in list(p_dir.glob("*.yaml")) + list(p_dir.glob("*.yml")):
                        if yf.stem not in seen_stems:
                            seen_stems.add(yf.stem)
                            found_files.append(yf)

    return found_files

def sync_instincts(threshold: float = CONFIDENCE_THRESHOLD, table: str = PROJECT_TABLE, project_id: str = "") -> Dict[str, Any]:
    """
    Evaluate instincts across global and project-scoped homunculus stores
    and promote those meeting the confidence threshold to LanceDB.
    """
    primary_dir = get_homunculus_dir()
    yaml_files = discover_instinct_files(project_id=project_id)

    results = {
        "homunculus_dir": str(primary_dir),
        "threshold": threshold,
        "scanned": len(yaml_files),
        "promoted": 0,
        "held": 0,
        "details": [],
    }

    if not yaml_files:
        results["message"] = f"No instinct files found across candidate homunculus directories."
        return results

    for yf in yaml_files:
        try:
            content = yf.read_text(encoding="utf-8")
            meta = parse_simple_yaml_frontmatter(content)
            confidence = float(meta.get("confidence", 0.5))
            instinct_id = meta.get("id") or yf.stem
            title = meta.get("name") or meta.get("trigger") or instinct_id
            scope = meta.get("scope", "project")
            pid = meta.get("project_id", "")

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
                        "project_id": pid,
                        "trust_state": "confirmed",
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
